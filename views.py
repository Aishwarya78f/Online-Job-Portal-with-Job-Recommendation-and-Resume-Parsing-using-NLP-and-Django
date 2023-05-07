from django.shortcuts import render,redirect
from pyresparser import ResumeParser
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from docx import Document
import requests
from django.http import HttpResponse
from django.db import models
from .models import*
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import io
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from datetime import date
import os
import chardet
import csv
import pandas as pd
import re
from ftfy import fix_text
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import os
import requests
# Create your views here.

def index(request):
    return render(request,'index.html')
@csrf_exempt
def submit_parse(request):
    url="http://127.0.0.1:5000/"

    
    response=requests.get(url)
    
    return HttpResponse(response.text)
    
def admin_login(request):
     error=""
     if request.method=="POST":
        u =  request.POST['uname']
        p = request.POST['pwd']
        user=authenticate(username=u,password=p)
        try:
             if user.is_staff:
                  login(request,user)
                  error="no"
             else:
                  error="yes"
        except:
             error="yes"
     d={'error':error}
     return render(request,'admin_login.html',d)


def user_login(request):
    error= ""
    if request.method == "POST":
        u = request.POST['uname'];
        p = request.POST['pwd'];
        user = authenticate(username=u,password=p)
        if user:
            try:
                user1 = StudentUser.objects.get(user=user)
                if user1.type == "student":
                    login(request,user)
                    error = "no"
                else:
                    error = "yes"
            except:
                error = "yes"
        else:
            error = "yes"
    d = {'error' : error}
    return render(request,'user_login.html',d)

def job_searcher(request):
    stopw = set(stopwords.words('english'))
    print(os.getcwd())
    df = pd.read_csv("media/job_final.csv")
    d={}
    df['test'] = df['Job_Description'].apply(
        lambda x: ' '.join([word for word in str(x).split() if len(word) > 2 and word not in (stopw)]))


    if request.method == 'POST':

        # print(request.POST.form['list_jobs'])

        resume = list(request.POST.get('list_jobs').split())
        print(type(resume))
        skills = []
        skills.append(' '.join(word for word in resume))
        org_name_clean = skills

        def ngrams(string, n=3):
            string = fix_text(string)  # fix text
            string = string.encode("ascii", errors="ignore").decode()  # remove non ascii chars
            string = string.lower()
            chars_to_remove = [")", "(", ".", "|", "[", "]", "{", "}", "'"]
            rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
            string = re.sub(rx, '', string)
            string = string.replace('&', 'and')
            string = string.replace(',', ' ')
            string = string.replace('-', ' ')
            string = string.title()  # normalise case - capital at start of each word
            string = re.sub(' +', ' ', string).strip()  # get rid of multiple spaces and replace with a single
            string = ' ' + string + ' '  # pad names for ngrams...
            string = re.sub(r'[,-./]|\sBD', r'', string)
            ngrams = zip(*[string[i:] for i in range(n)])
            return [''.join(ngram) for ngram in ngrams]

        vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
        tfidf = vectorizer.fit_transform(org_name_clean)
        print('Vecorizing completed...')

        def getNearestN(query):
            queryTFIDF_ = vectorizer.transform(query)
            distances, indices = nbrs.kneighbors(queryTFIDF_)
            return distances, indices

        nbrs = NearestNeighbors(n_neighbors=1, n_jobs=-1).fit(tfidf)
        unique_org = (df['test'].values)
        distances, indices = getNearestN(unique_org)
        unique_org = list(unique_org)
        matches = []
        for i, j in enumerate(indices):
            dist = round(distances[i][0], 2)

            temp = [dist]
            matches.append(temp)
        matches = pd.DataFrame(matches, columns=['Match confidence'])
        df['match'] = matches['Match confidence']
        df1 = df.sort_values('match')
        df2 = df1[['Position', 'Company', 'Location']].head(10).reset_index()
        context = {'tables': [df2.to_html(classes='job')], 'titles': ['na', 'Job']}
        return render(request, 'new_model.html', context)

    return render(request, 'new_model.html')

def resume_parser(request):
    df =pd.read_csv('media/job_final.csv') 
    stopw  = set(stopwords.words('english'))
    df['test']=df['Job_Description'].apply(lambda x: ' '.join([word for word in str(x).split() if len(word)>2 and word not in (stopw)]))
    if request.method == 'POST':
        userfile = request.FILES['userfile']
        file_path = os.path.join(settings.MEDIA_ROOT, userfile.name)
        with open(file_path, 'wb') as f:
            for chunk in userfile.chunks():
                f.write(chunk)
        try:
            doc = Document()
            with open(file_path, 'r') as file:
                doc.add_paragraph(file.read())
                doc.save("text.docx")
                data = ResumeParser('text.docx').get_extracted_data()
        except:
            data = ResumeParser(file_path).get_extracted_data()
        resume = data['skills']
        print(type(resume))
    
        skills=[]
        skills.append(' '.join(word for word in resume))
        org_name_clean = skills
        
        def ngrams(string, n=3):
            string = fix_text(string) # fix text
            string = string.encode("ascii", errors="ignore").decode() #remove non ascii chars
            string = string.lower()
            chars_to_remove = [")","(",".","|","[","]","{","}","'"]
            rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
            string = re.sub(rx, '', string)
            string = string.replace('&', 'and')
            string = string.replace(',', ' ')
            string = string.replace('-', ' ')
            string = string.title() # normalise case - capital at start of each word
            string = re.sub(' +',' ',string).strip() # get rid of multiple spaces and replace with a single
            string = ' '+ string +' ' # pad names for ngrams...
            string = re.sub(r'[,-./]|\sBD',r'', string)
            ngrams = zip(*[string[i:] for i in range(n)])
            return [''.join(ngram) for ngram in ngrams]
        vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
        tfidf = vectorizer.fit_transform(org_name_clean)
        print('Vecorizing completed...')
        
        
        def getNearestN(query):
          queryTFIDF_ = vectorizer.transform(query)
          distances, indices = nbrs.kneighbors(queryTFIDF_)
          return distances, indices
        nbrs = NearestNeighbors(n_neighbors=1, n_jobs=-1).fit(tfidf)
        unique_org = (df['test'].values)
        distances, indices = getNearestN(unique_org)
        unique_org = list(unique_org)
        matches = []
        for i,j in enumerate(indices):
            dist=round(distances[i][0],2)
  
            temp = [dist]
            matches.append(temp)
        matches = pd.DataFrame(matches, columns=['Match confidence'])
        df['match']=matches['Match confidence']
        df1=df.sort_values('match')
        df2=df1[['Position', 'Company','Location']].head(10).reset_index()
        context = {'tables': [df2.to_html(classes='job')], 'titles': ['na', 'Job']}
        return render(request, 'model.html', context)

    return render(request, 'model.html')
        
        
        
        
        
    #return  'nothing' 
    

    # return  'nothing'


def recruiter_login(request):
    error= ""
    if request.method == "POST":
        u = request.POST['uname'];
        p = request.POST['pwd'];
        user = authenticate(username=u,password=p)
        if user:
            try:
                user1 = Recruiter.objects.get(user=user)
                if user1.type == "recruiter" and user1.status!="pending":
                    login(request,user)
                    error = "no"
                else:
                    error = "not"
            except:
                error = "yes"
    d = {'error' : error}
    return render(request,'recruiter_login.html',d)

def recruiter_signup(request):
    error= ""
    if request.method == "POST":
        f = request.POST['fname']
        l = request.POST['lname']
        i = request.FILES['image']
        p = request.POST['pwd']
        e = request.POST['email']
        con = request.POST['contact']
        gen = request.POST['gender']
        company = request.POST['company']
        try:
            user = User.objects.create_user(first_name=f,last_name=l,username=e,password=p)
            Recruiter.objects.create(user=user,mobile=con,image=i,gender=gen,company=company,type="recruiter",status="pending")
            error = "no"
        except:
            error = "yes"
    d={'error': error}
    return render(request,'recruiter_signup.html',d)

def user_home(request):
    if not request.user.is_authenticated:
        return redirect('user_login')
    user = request.user
    student = StudentUser.objects.get(user=user)
    error= ""
    if request.method == "POST":
        f = request.POST['fname']
        l = request.POST['lname']
        con = request.POST['contact']
        gen = request.POST['gender']
        student.user.first_name = f
        student.user.last_name = l
        student.user.mobile = con
        student.user.gender = gen
        try:
            student.save()
            student.user.save()
            error = "no"
        except:
            error = "yes"

        try:
            i = request.FILES['image']
            student.image = i
            student.save()
            error = "no"
        except:
            pass
    
    d={'student':student,'error':error}
    return render(request,'user_home.html',d)

def Logout(request):
    logout(request)
    return redirect('index')

def user_signup(request):
    error= ""
    if request.method == "POST":
        f = request.POST['fname']
        l = request.POST['lname']
        i = request.FILES['image']
        p = request.POST['pwd']
        e = request.POST['email']
        con = request.POST['contact']
        gen = request.POST['gender']
        try:
            user = User.objects.create_user(first_name=f,last_name=l,username=e,password=p)
            StudentUser.objects.create(user=user,mobile=con,image=i,gender=gen,type="student")
            error = "no"
        except:
            error = "yes"
    d={'error': error}
    return render(request,'user_signup.html',d)

def recruiter_home(request):
    if not request.user.is_authenticated:
        return redirect('recruiter_login')
    user = request.user
    recruiter = Recruiter.objects.get(user=user)
    error= ""
    if request.method == "POST":
        f = request.POST['fname']
        l = request.POST['lname']
        con = request.POST['contact']
        gen = request.POST['gender']
        recruiter.user.first_name = f
        recruiter.user.last_name = l
        recruiter.user.mobile = con
        recruiter.user.gender = gen
        try:
            recruiter.save()
            recruiter.user.save()
            error = "no"
        except:
            error = "yes"

        try:
            i = request.FILES['image']
            recruiter.image = i
            recruiter.save()
            error = "no"
        except:
            pass

    d={'recruiter':recruiter,'error':error}
    return render(request,'recruiter_home.html',d)
    
def admin_home(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     return render(request,'admin_home.html')

def view_users(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     data = StudentUser.objects.all()
     d = {'data':data}
     return render(request,'view_users.html',d)

def delete_user(request,pid):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     student = User.objects.get(id=pid)
     student.delete()
     return redirect('view_users')

def delete_recruiter(request,pid):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     recruiter = User.objects.get(id=pid)
     recruiter.delete()
     return redirect('recruiter_all')

def recruiter_pending(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     data = Recruiter.objects.filter(status="pending")
     d = {'data':data}
     return render(request,'recruiter_pending.html',d)

def change_status(request,pid):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     error=""
     recruiter = Recruiter.objects.get(id=pid)
     if request.method == "POST":
        s = request.POST['status']
        recruiter.status=s
        try:
            recruiter.save()
            error="no"
        except:
            error="yes"
     d = {'recruiter':recruiter,'error':error}
     return render(request,'change_status.html',d)

def recruiter_accepted(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     data = Recruiter.objects.filter(status='Accept')
     d = {'data':data}
     return render(request,'recruiter_accepted.html',d)

def recruiter_rejected(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     data = Recruiter.objects.filter(status='Reject')
     d = {'data':data}
     return render(request,'recruiter_rejected.html',d)

def recruiter_all(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     data = Recruiter.objects.all()
     d = {'data':data}
     return render(request,'recruiter_all.html',d)

def change_passwordadmin(request):
     if not request.user.is_authenticated:
        return redirect('admin_login')
     error=""
     if request.method == "POST":
        c = request.POST['currentpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(c):
                u.set_password(n)
                u.save()
                error="no"
            else:
                error="not"
        except:
            error="yes"
     d = {'error':error}
     return render(request,'change_passwordadmin.html',d)

def change_passworduser(request):
     if not request.user.is_authenticated:
        return redirect('user_login')
     error=""
     if request.method == "POST":
        c = request.POST['currentpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(c):
                u.set_password(n)
                u.save()
                error="no"
            else:
                error="not"
        except:
            error="yes"
     d = {'error':error}
     return render(request,'change_passworduser.html',d)

def change_passwordrecruiter(request):
     if not request.user.is_authenticated:
        return redirect('recruiter_login')
     error=""
     if request.method == "POST":
        c = request.POST['currentpassword']
        n = request.POST['newpassword']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(c):
                u.set_password(n)
                u.save()
                error="no"
            else:
                error="not"
        except:
            error="yes"
     d = {'error':error}
     return render(request,'change_passwordrecruiter.html',d)

def add_job(request):
     if not request.user.is_authenticated:
        return redirect('recruiter_login')
     error= ""
     if request.method == "POST":
        jt = request.POST['jobtitle']
        sd = request.POST['startdate']
        ed = request.POST['enddate']
        sal = request.POST['salary']
        l = request.FILES['logo']
        exp = request.POST['experience']
        loc = request.POST['location']
        skills = request.POST['skills']
        des = request.POST['description']
        user= request.user
        recruiter=Recruiter.objects.get(user=user)
        try:
            Job.objects.create(recruiter=recruiter,start_date=sd,end_date=ed,title=jt,salary=sal,image=l,description=des,experience=exp,location=loc,skills=skills,creationdate=date.today())
            error = "no"
        except:
            error = "yes"
     d={'error': error}
     return render(request,'add_job.html',d)

def job_list(request):
     if not request.user.is_authenticated:
        return redirect('recruiter_login')
     user= request.user
     recruiter=Recruiter.objects.get(user=user)
     job=Job.objects.filter(recruiter=recruiter)
     d={'job':job}
     return render(request,'job_list.html',d)

def edit_jobdetail(request,pid):
     if not request.user.is_authenticated:
        return redirect('recruiter_login')
     error= ""
     job=Job.objects.get(id=pid)
     if request.method == "POST":
        jt = request.POST['jobtitle']
        sd = request.POST['startdate']
        ed = request.POST['enddate']
        sal = request.POST['salary']
        exp = request.POST['experience']
        loc = request.POST['location']
        skills = request.POST['skills']
        des = request.POST['description']
        job.title = jt
        job.salary=sal
        job.experience=exp
        job.location=loc
        job.skills=skills
        job.description=des
        try:
            job.save()
            error = "no"
        except:
            error = "yes"
        
        if sd:
            try:
                job.start_date = ed
                job.save()

            except:
                pass
        else:
            pass
        
        if ed:
            try:
                job.end_date = ed
                job.save()

            except:
                pass
        else:
            pass
     d={'error': error,'job':job}
     return render(request,'edit_jobdetail.html',d)

def change_companylogo(request,pid):
     if not request.user.is_authenticated:
        return redirect('recruiter_login')
     error= ""
     job=Job.objects.get(id=pid)
     if request.method == "POST":
        cl=request.FILES['logo']
        job.image=cl
        try:
            job.save()
            error = "no"
        except:
            error = "yes"
     d={'error': error,'job':job}
     return render(request,'change_companylogo.html',d)

def latest_jobs(request):
    job = Job.objects.all().order_by('-start_date')
    d = {'job':job}
    return render(request,'latest_jobs.html',d)

def user_latestjobs(request):
    job = Job.objects.all().order_by('-start_date')
    user = request.user
    student = StudentUser.objects.get(user=user)
    data = Apply.objects.filter(student=student)
    li = []
    for i in data:
        li.append(i.job.id)
    d = {'job':job,'li':li}
    return render(request,'user_latestjobs.html',d)

def job_detail(request,pid):
    job = Job.objects.get(id=pid)
    d = {'job':job}
    return render(request,'job_detail.html',d)

def applied_candidatelist(request):
    if not request.user.is_authenticated:
        return redirect('recruiter_login')
    
    data = Apply.objects.all()
    d = {'data':data}
    return render(request,'applied_candidatelist.html',d)

def applyforjob(request):
    if not request.user.is_authenticated:
        return redirect('recruiter_login')
    
    data = Apply.objects.all()
    d = {'data':data}
    return render(request,'applied_candidatelist.html',d)
def applyforjob(request,pid):
     if not request.user.is_authenticated:
        return redirect('user_login')
     error= ""
     user=request.user
     student=StudentUser.objects.get(user=user)
     job=Job.objects.get(id=pid)
     date1 = date.today()
     if job.end_date < date1:
         error ="close"
     elif job.start_date > date1:
         error ="notopen"
     else:
        if request.method == "POST":
           r =request.FILES['resume']
           Apply.objects.create(job=job,student=student,resume=r,applydate=date.today())
           error="done"
         
     
     d={'error': error}
     return render(request,'applyforjob.html',d)