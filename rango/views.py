from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import UserProfile
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm,UserProfileForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect

def encode_url(str):
    return str.replace(' ', '_')

def decode_url(str):
    return str.replace('_', ' ')

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__startswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if (len(cat_list) > max_results):
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = encode_url(cat.name)

    return cat_list


def index(request):
	context = RequestContext(request)

	top_category_list = Category.objects.order_by('-likes')[:5]

	for category in top_category_list:
		category.url = encode_url(category.name)

	context_dict = {'categories': top_category_list}

	cat_list = get_category_list()
	context_dict['cat_list'] = cat_list

	for category in top_category_list:
		category.url = category.name.replace(' ', '_')
	#context_dict = {'bold message': "it is fun while you work it"}

	  	page_list = Page.objects.order_by('-views')[:5]
	  	context_dict['pages'] = page_list

	#return render_to_response('rango/index.html', context_dict, context)
	#return HttpResponse('Rango says work up your code real well \t <a href="rango/about/">About</a>')
	#visits = int(request.session.get('visits', '0'))

	if request.session.get('last_visit'):
		last_visit = request.session.get('last_visit')

       	visits = request.session.get('visits', 0)

        #if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
         #   request.session['visits'] = visits + 1

        #else:
        # The get returns None, and the session does not have a value for the last visit.
	        #request.session['last_visit'] = str(datetime.now())
	        #request.session['visits'] = 1

	return render_to_response('rango/index.html', context_dict, context)


def about(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list

    count = request.session.get('visits', 0)

    context_dict['visit_count'] = count

    return render_to_response('rango/about.html', context_dict, context)


def category(request, category_name_url):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list

    category_name = decode_url(category_name_url)
	#category_name = category_name_url.replace('_', ' ')
    context_dict = {'category_name': category_name,
					 'category_name_url': category_name_url}

    try:
		category = Category.objects.get(name__iexact=category_name)
		context_dict['category'] = category

		pages = Page.objects.filter(category=category).order_by('-views')

		context_dict['pages']=pages

		#context_dict['category']=category

    except Category.DoesNotExist:

        pass

        if request.method == 'POST':
	  		query = request.POST.get('query')
        if query:
            query = query.strip()
            result_list = run_query(query)
            context_dict['result_list'] = result_list

    return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
	context = RequestContext(request)
	cat_list = get_category_list()
  	context_dict = {}
  	context_dict['cat_list'] = cat_list


	if request.method =='POST':
		form = CategoryForm(request.POST)

		if form.is_valid():
			form.save(commit=True)

			return index(request)
		else:
			print form.errors
	else:
		form = CategoryForm()

	context_dict['form'] = form
	return render_to_response('rango/add_category.html', context_dict, context)

@login_required
def add_page(request, category_name_url):
	context = RequestContext(request)
	cat_list = get_category_list()
   	context_dict = {}
   	context_dict['cat_list'] = cat_list

	category_name = decode_url(category_name_url)

	if request.method =='POST':
		form = PageForm(request.POST)

		if form.is_valid():
			page = form.save(commit=False)


			try:
				cat = Category.objects.get(name= category_name)
				page.category = cat
			except Category.DoesNotExist:
				return render_to_response('rango/add_category.html', {}, context)
			
			page.views = 0
			page.save()

			return category(request, category_name_url)
		else:
			print form.errors
	else:
		form = PageForm()

	return render_to_response('rango/add_page.html',
		{'category_name_url': category_name_url,
		 'category_name': category_name, 'form':form}, context)

def register(request):
	#if request.session.test_cookie_worked():
	#	print "****TEST COOKIE WORKED****"
	#	request.session.delete_test_cookie()
	context = RequestContext(request)
	cat_list = get_category_list()
   	context_dict = {}
   	context_dict['cat_list'] = cat_list

	registered = False

	if request.method =='POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		if user_form.is_valid() and profile_form.is_valid():
		
			user = user_form.save()
	    	user.set_password(user.password)
	    	user.save()

	    	profile = profile_form.save(commit=False)
	    	profile.user =user

	    	if 'picture' in request.FILES:
	    		profile.picture = request.FILES['picture']

	    		profile.save()
	    		registered = True

	    	else:
	    		print user_form.errors, profile_form.errors

	else:
		user_form = UserForm()
		profile_form = UserProfileForm()


	context_dict['user_form'] = user_form
	context_dict['profile_form']= profile_form
	context_dict['registered'] = registered

	return render_to_response('rango/register.html', context_dict, context)

@login_required
def user_login(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list

    # If HTTP POST, pull out form data and process it.
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        #user authentication
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
           
            else:
                context_dict['disabled_account'] = True
                return render_to_response('rango/login.html', context_dict, context)
        # Invalid login details supplied!
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            context_dict['bad_details'] = True

    else:
    	return render_to_response('rango/login.html', context_dict, context)

@login_required
def restricted(request):
	context = RequestContext(request)
	cat_list = get_category_list()
   	context_dict = {}
   	context_dict['cat_list'] = cat_list

    	return HttpResponse('rango/restricted.html', context_dict, context)

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/rango/')

def search(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    context_dict['result_list'] = result_list
    return render_to_response('rango/search.html', context_dict, context)


@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}
    u = User.objects.get(username=request.user)
    
    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None
    
    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'

    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']

            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url

            except:

                pass

    return redirect(url)

@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None

    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0

    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            category.save()

    return HttpResponse(likes)

def suggest_category(request):
    context = RequestContext(request)
    cat_list = []
    starts_with = ''

    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    else:
        starts_with = request.POST['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render_to_response('rango/category_list.html', {'cat_list': cat_list }, context)


@login_required
def auto_add_page(request):
    context = RequestContext(request)
    cat_id = None
    url = None
    title = None
    context_dict = {}

    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages

    return render_to_response('rango/page_list.html', context_dict, context)

