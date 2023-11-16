import requests
from bs4 import BeautifulSoup
import re

def get_subj(degrs_html_str:str,str_to_search:str,start:int,offset_to_subj:int)->str:
    """
    Retrieves the subject of the degree program from the given html
    @param degrs_html : html with degree program information
    @param str_to_search : unique part of the html to search for to bring index i closer to subject text
    @param start : starting index of degrs_html_str for find() method to start looking for str_to_search
    @param offset_to_subject : offset needed to get i to be the index of the first character of subject
    """
    subj = ''
    i = degrs_html_str.find(str_to_search,start)+offset_to_subj
    while degrs_html_str[i]!='<':
        subj+=degrs_html_str[i]
        i+=1
    return subj

def get_degr_url_and_abbrv(degrs_html_str:str,col_num:int,start:int):
    href_ind = degrs_html_str.find('href',start)
    abbrv_ind = degrs_html_str.find('>',href_ind)
    #if there is a link to a degree program (which is in the href tag) in the current column 
    if href_ind>0 and href_ind<degrs_html_str.find('column'+str(col_num+1)):
        i=0
        degr_url = ''
        abbrv = ''
        i=href_ind+6
        while degrs_html_str[i]!='\"':
            degr_url+=degrs_html_str[i]
            i+=1
        #next move i to where the abbrev is
        i=abbrv_ind+1
        while degrs_html_str[i]!='<':
            abbrv+=degrs_html_str[i]
            i+=1

        #i is returned to use in making it faster to find the next starting index (where 'column#' is)
        return degr_url, abbrv,i

    return '', '',start

def get_degr_progs()->dict:
    """
    Retrieves all degree programs at Temple University from its Academic Bulletin
    """
    #Remember to use the keys from the return for the dropdown list when finished this function
    degr_program_to_url = dict()
    try: 
        req = requests.get("https://bulletin.temple.edu/academic-programs/")
        req.raise_for_status()
        soup = BeautifulSoup(req.content,'html.parser')
        degr_programs_htmls = soup.find('tbody', class_='fixedTH',id='degree_body')
        for html in degr_programs_htmls:
            degrs_html_str = str(html)
            #special case for first row where the style is being set (html has extra stuff)
            if 'style' in degrs_html_str:
                subj = get_subj(degrs_html_str,'>',degrs_html_str.find('column0'),1)
                next_col_str_search_start_ind = 0
                for i in range(1,4):
                    degr_url, abbrv, next_col_str_search_start_ind = get_degr_url_and_abbrv(degrs_html_str, i,degrs_html_str.find('column' + str(i),next_col_str_search_start_ind))
                    if not degr_url.isspace():
                        #modify to include abbrv with subject
                        degr_program_to_url[subj]=(degr_url, abbrv)
            elif not html.text.isspace():
                subj = get_subj(degrs_html_str,'column0',0,9)
                next_col_str_search_start_ind = 0
                for i in range(1,4):
                    degr_url, abbrv, next_col_str_search_start_ind = get_degr_url_and_abbrv(degrs_html_str, i,degrs_html_str.find('column' + str(i),next_col_str_search_start_ind))
                    if not degr_url.isspace():
                        #modify to include abbrv with subject
                        degr_program_to_url[subj]=(degr_url, abbrv)
            
        return degr_program_to_url
    
    except requests.exceptions.Timeout as e:
        print(f"Timeout occurred: {e}")
    
    #return none if error occurred
    return dict()

#degree_program will need to be formatted specifically for certain degree programs, but for most it can be assumed to just join the phrases with a '-'
def get_curric(degr_program:str)->list[str]:
    """
    Retrieves the curriculum for the specified degree program
    @param degr_program : the name of the degree program to retrieve required courses for
    """
    #create dictionary to match up level and school to each degree program
    level = 'undergraduate/'
    school = 'science-technology/'
    req = requests.get("https://bulletin.temple.edu/" + level +school+ '-'.join(degr_program.lower().split()) + "/#requirementstext")
    soup=BeautifulSoup(req.content,'html.parser')
    requirements_html = soup.find('div',id='requirementstextcontainer')
    courses_html = requirements_html.find_all('a',class_='bubblelink code')
    curric = []
    for c in courses_html:
        #can later account for the "\xa0" in the middle of each, but printing each element produces the desired format
        curric.append(c.text)
    return curric

def get_term_codes()->dict:
    """
    Retrieves the numbers used to specify the semester in url queries
    Credit: Neil Conley (Github: gummyfrog)
    """
    PAGINATION_OPTS = {
     "offset": "1",
     "max": "10",
    }
    response = requests.get("https://prd-xereg.temple.edu/StudentRegistrationSsb/ssb/classSearch/getTerms", PAGINATION_OPTS)
    return(response.json())

def get_course_sections_info(term_code:str,subj:str,course_num:str,attr='')->dict:
    """
    Retrieves info on the sections available during the specified term for the specified class
    @param term_code : number representing the semester
    @param subject : abbreviation representing the subject of the course
    @param course_num : number of the course
    @param attr : attribute of the course (i.e. GU for Gened United States or GY for Intellectual Heritage I)
    Credit: https://github.com/gummyfrog/TempleBulletinBot
    """
    session = requests.Session()
    # term and txt_term need to be the same
    SEARCH_REQ = {
        "term": term_code,
        "txt_term": term_code,
        "txt_subject": subj,
        "txt_courseNumber": course_num,
        "txt_attribute": attr
    }
    # extra stuff for the results
    RESULTS_OPTS = {
        "pageOffset": 0,
        "pageMaxSize": 10,
        "sortColumn": "subjectDescription",
        "sortDirection": "asc",
    }

    RESULTS_ARGS = dict()
    RESULTS_ARGS.update(SEARCH_REQ)
    RESULTS_ARGS.update(RESULTS_OPTS)

    # Establish session
    session.post("https://prd-xereg.temple.edu/StudentRegistrationSsb/")
    # Select a term
    session.post("https://prd-xereg.temple.edu/StudentRegistrationSsb/ssb/term/search?mode=search", SEARCH_REQ)
    # Start subject search for the chosen term
    session.post("https://prd-xereg.temple.edu/StudentRegistrationSsb/ssb/classSearch/get_subject?offset=1&max=10", SEARCH_REQ)
    # Clear old results, if any
    session.post("https://prd-xereg.temple.edu/StudentRegistrationSsb/ssb/classSearch/resetDataForm")
    # Execute search
    response = session.post("https://prd-xereg.temple.edu/StudentRegistrationSsb/ssb/searchResults/searchResults?startDatepicker=&endDatepicker=", RESULTS_ARGS)

    data = response.json()
    data["ztcEncodedImage"] = ""
    return data

#can retrieve other info such as "Would take again" and difficulty later on if it helps
def get_rmp_data(prof:str):
    """
    Retrieves information from ratemyprofessors.com related to the specified professor's ratings
    @param prof : professor to retrieve information about on ratemyprofessors.com
    """
    prof_search_req = requests.get("https://www.ratemyprofessors.com/search/professors/999?q="+'%20'.join(prof.split()))
    #credit to Nobelz in https://github.com/Nobelz/RateMyProfessorAPI for retrieval of RMP professor ids
    prof_ids = re.findall(r'"legacyId":(\d+)', prof_search_req.text)
    #loops through the professor ids found based on search by professsor name
    for id in prof_ids:
        try:
            prof_rating_req = requests.get("https://www.ratemyprofessors.com/professor/" + id)
            soup=BeautifulSoup(prof_rating_req.content,'html.parser')
            #rating retrieval
            rating_html = str(soup.find("div",re.compile("^RatingValue__Numerator")))
            rating = ''
            i = rating_html.rfind('<')-1
            while rating_html[i]!='>':
                rating+=rating_html[i]
                i-=1
            rating = rating[::-1]
            #retrieval of number of ratings
            num_ratings=''
            num_reviews_html = str(soup.find("div",re.compile("^RatingValue__NumRatings")))
            i=num_reviews_html.rfind('\">')+2
            while num_reviews_html[i]!='<':
                num_ratings+=num_reviews_html[i]
                i+=1
            return [rating,num_ratings]
        except:
            pass

#get_degr_progs()
#print(get_curric("Computer Science BS"))
#print(get_term_codes())
#print(get_course_sections_info("202336","EES","2021",''))
#print(get_rmp_rating("Sarah Stapleton"))