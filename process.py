#!/usr/bin/python3

import bs4 as bs
import pprint
import argparse
import sys, re
import time, datetime
import json
from subprocess import call

fields = [
    'title',
    'url',
    'name',
    'code',
    'f_source',
    'f_amount',
    'period',
    'comments']

def prettify(html, output_file, template_file):
    doc = bs.BeautifulSoup(html, 'html.parser')

    # build a dictionary of institution names
    group_names = {}
    institution_names = {}
    for tag in doc.find_all('h2'):
        t = tag.text.strip()
        if (len(t) == 0 or t.find(" - ") == -1): continue # not an affiliation
        institution_names[t] = t.split(' - ')[-1].strip().lower().replace(' ', '_')
        group_names[t] = t.split(' - ')[0].strip().lower().replace(' ', '_')        
    pprint.pprint(f"Found {len(group_names)} groups:\n {group_names}")
    pprint.pprint(f"Found {len(institution_names)} groups:\n {institution_names}")
    
    # remove comments
    for tag in doc.find_all('sup'):
        tag.decompose()

    # remove empty tags
    for tag in doc.find_all('span'):
        if tag.text.strip() == '':
            tag.decompose()
    for tag in doc.find_all('p'):
        if tag.text.strip() == '':
            tag.decompose()
    # google likes to intercept links; retain only contents
    for tag in doc.find_all('a'):
        tag.unwrap()        
    
    # remove middlemen-container tags; this may need to be done a few times
    for i in range(5):
      for tag in doc.find_all('span'):
          tag.unwrap()
      for tag in doc.find_all('p'):
          tag.unwrap()
      
    # second column in tags is description of 1st; remove and rely on correctly ordered 
    for tag in doc.find_all('table'):
        parts = tag.find_all('tr')
        for part, field in zip(parts, fields):
            if (len(part.contents) > 1):
                part.find_all('td')[1].decompose()
            part.attrs = {'class': field}
    
    # more unwrapping
    for tag in doc.find_all('td'):
        tag.unwrap()       
    for tag in doc.find_all('h3'):
        tag.unwrap()
    for tag in doc.find_all('h4'):
        tag.unwrap()
       
    # add institution to project divs
    for tag in doc.find_all('table'):
        found_who = False
        bad_who = False
        for sibling in tag.previous_siblings:
            if sibling.name == 'h2':
                who = sibling.text.strip()
                if not who in group_names or not who in institution_names:
                  print(f"Weird group/institution ({who}) for project {tag}, skipping!")
                  bad_who = True
                  break
                found_who = True
                tag.attrs = {'class': 'project', 
                             'data-group': group_names[who],
                             'data-institution': institution_names[who]}
                break
        if not found_who and not bad_who:
            print(f"FATAL -- Could not find institution for project {tag}")
            sys.exit(1)
        elif bad_who:
            continue
        else:
            print(f"==> Found project for {group_names[who]}")
        
        print(f"\tFinding ES/EN alternatives")
        for part in tag.find_all('tr'):
            
            # also interpret ES: EN: as two spans
            t = part.text.strip()
            if (re.match("ES:", t) or re.match("EN:", t)):
                print(f"\thave a candidate! '{t}'!")
                # https://pythex.org/
                es_en = re.match(r'\s*ES:\s*(\w.*)\s*EN:\s*(\w.*)\s*', t)
                if (es_en is not None):
                    t_es = es_en.group(1)
                    t_en = es_en.group(2)
                    part.string = ''
                    print(f"\t\t--{t_es}\n\t\t++{t_en}")
                    classes = part.get_attribute_list('class')
                    
                    tag_es = doc.new_tag("span")
                    tag_es.string = t_es
                    tag_es.attrs = {'class': [classes[0], 'es']}
                    tag_en = doc.new_tag("span")
                    tag_en.string = t_en
                    tag_en.attrs = {'class': [classes[0], 'en']}
                    part.replace_with(tag_es)
                    tag_es.insert_after(tag_en)
                else:       
                    print(f"\t ... false alarm :-(")
                    part.name = 'span'
            else:
                part.name = 'span'        
        
        title = tag.find('span', 'title')
        print(f"\tFound {title}")
        header = title.wrap(doc.new_tag("div"))
        header.attrs = {'class': ['header']}
                
        for u in tag.find_all('span', 'url'):
          t = u.text.strip()
          if len(t) == 0: continue
          print(f"\t ... fixin' {t}");
          u.extract() 
          for ut in t.split("http"):
            if len(ut) == 0: continue # ignore empty 1st
            ut = f"http{ut}"
            uu = doc.new_tag('a')
            uu['href'] = ut
            uu.string = '🔗'            
            header.append(uu)          
        
        tag.name = 'div'        
        print(" ... project ready")

    # save project divs to file
    project_divs = []
    counter = 0
    for tag in doc.find_all('div'):
        if (tag.attrs.get('class') == 'project'):
            if (tag.attrs.get('data-group') != 'ejemplo'):
                counter += 1
                project_divs.append(tag.prettify())
                    
    # output using template
    with open(template_file, 'r') as template_f:
        template = template_f.read()
        
    template = template.replace("$GROUPS_GO_HERE$", 
      json.dumps(group_names, sort_keys=True, indent=4,ensure_ascii=False))
    
    template = template.replace("$INSTITUTIONS_GO_HERE$",
      json.dumps(institution_names, sort_keys=True, indent=4,ensure_ascii=False))
    
    template = template.replace("$PROJECTS_GO_HERE$", "\n".join(project_divs))
    with open(output_file, 'w') as output_f:
        output_f.write(template)                    

    print(f"File saved as {output_file} with {counter} projects")

if __name__ == '__main__':      
    parser = argparse.ArgumentParser(description=\
        "Convert a Google Doc saved as html to clean html that can be used in publishing")
    parser.add_argument("--html_file", 
            help="The input file", default="Proyectosparalaweb.html")  
    parser.add_argument("--output_file", 
            help="The output file", default="proyectos.html") 
    parser.add_argument("--template_file", 
            help="Template html to use for output file", default="template.html")                
    args = parser.parse_args()
    with open(args.html_file, 'r', encoding='utf-8') as file:
        prettify(file.read(), args.output_file, args.template_file)

