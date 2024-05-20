from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import PyPDF2
from fastapi import File, UploadFile
from io import BytesIO



app = FastAPI()

# Define custom exceptions
class UsernameError(Exception):
    pass

class PlatformError(Exception):
    pass

# Define User class
class User:
    def __init__(self, username=None, platform=None):
        self.__username = username
        self.__platform = platform

    def codechef(self):
        url = f"https://codechef.com/users/{self.__username}"
        session = HTMLSession()
        d = dict()
        r = session.get(url, timeout=10)
        d['username'] = self.__username
        if r.status_code != 200:
            raise UsernameError("User not found")
        try:
            rating_header = r.html.find(".rating-header", first=True)
        except:
            raise UsernameError('User not found')

        try:
            rating = rating_header.find(".rating-number", first=True).text
            d["rating"] = rating
        except:
            raise UsernameError('User not found')
        max_rating = rating_header.find('small')[0].text[1:-1].split()[2]
        rating_star = len(r.html.find(".rating-star", first=True).find('span'))
        ranks = r.html.find('.rating-ranks', first=True).find('strong')
        global_rank = ranks[0].text
        country_rank = ranks[1].text
        d["global_rank"] = global_rank
        d["country_rank"] = country_rank
        return d

    def codeforces(self):
        url = f'https://codeforces.com/api/user.info?handles={self.__username}'
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            raise UsernameError('User not found')
        r_data = r.json()
        if r_data['status'] != 'OK':
            raise UsernameError('User not found')
        d = dict()
        d['username'] = self.__username
        d['ranking'] = r_data['result'][0]['rank']
        d['maxRating'] = r_data['result'][0]['maxRating']
        return d

    def gfg(self):
        url = f"https://auth.geeksforgeeks.org/user/{self.__username}/?utm_source=geeksforgeeks"
        response = requests.get(url)
        d = dict()
        soup = BeautifulSoup(response.text, 'html.parser')
        if response.status_code != 200:
            d['username'] = "Please enter valid username and details"
            return d

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
        d['username'] = self.__username
        d['total_no_of_problems'] = soup.select('.scoreCard_head_card_left--score__pC6ZA')[0].text
        d['coding_score'] = soup.select('.scoreCard_head_card_left--score__pC6ZA')[1].text
        return d

    def leetcode(self):
        url = f"https://leetcode-stats-api.herokuapp.com/{self.__username}"
        r = requests.get(url)
        if r.status_code != 200:
            raise UsernameError('User not found')
        r_data = r.json()
        d = dict()
        d['username'] = self.__username
        d['totalSolved'] = r_data["totalSolved"]
        d['ranking'] = r_data["ranking"]
        d['acceptanceRate'] = r_data["acceptanceRate"]
        return d

    def github(self):
        url = f"https://api.github.com/users/{self.__username}"
        r = requests.get(url)
        if r.status_code != 200:
            raise UsernameError('User not found')
        r_data = r.json()
        url1 = f"https://api.github.com/users/{self.__username}/repos"
        r1 = requests.get(url1)
        if r1.status_code != 200:
            raise UsernameError('User not found')
        r1_data = r1.json()
        d = dict()
        d['username'] = r_data["login"]
        d['public_repos'] = r_data["public_repos"]
        dali = []
        for repo in r1_data:
            dali.append({"name": repo["name"], "url": repo["html_url"]})
        d['repos'] = dali
        return d

    def get_info(self):
        if self.__platform == 'codechef':
            return self.codechef()
        if self.__platform == 'codeforces':
            return self.codeforces()
        if self.__platform == 'leetcode':
            return self.leetcode()
        if self.__platform == 'gfg':
            return self.gfg()
        if self.__platform == 'github':
            return self.github()
        raise PlatformError('Platform not Found')

# Define Pydantic models for request validation
class UserRequest(BaseModel):
    username: str
    platform: str

@app.post("/get_info")
def get_user_info(request: UserRequest):
    try:
        user = User(username=request.username, platform=request.platform)
        data = user.get_info()
        return data
    except UsernameError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PlatformError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# For running PDF extraction as an API
@app.post("/extract_resume")
async def extract_resume(file: UploadFile = File(...)):
    try:
        # contents = await file.read()
        contents = await file.read()
        pdf_file = BytesIO(contents)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
    finally:
        await file.close()

  
      
   
