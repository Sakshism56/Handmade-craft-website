from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate,login,logout
from ecommapp.models import Product,Cart,Order
from django.db.models import Q
import random
import razorpay
from django.core.mail import send_mail

# Create your views here.
def product(request):
    p=Product.objects.filter(is_active=True)
    #print(p)
    context={}
    context['data']=p
    return render(request,'index.html',context)

def register(request):
    context={}
    if request.method=='GET':
        return render(request,'register.html')
    else:
        n=request.POST['uname']
        p=request.POST['upass']
        cp=request.POST['ucpass']

        #print(n)
        #print(p)
        #print(cp)
        if n=='' or p=='' or cp=='':
            context['errmsg']='Field can not be blank'
            return render(request,'register.html',context)
        elif len(p)<8:
            context['errmsg']='password must be atleast 8 character'
            return render(request,'register.html',context)
        elif p!=cp:
            context['errmsg']='password and confirm password must be same'
            return render(request,'register.html',context)
        else:
            try:
                u=User.objects.create(username=n,email=n)
                u.set_password(p)
                u.save()
                context['sucess']='User Create Successfully'
                return render(request,'register.html',context)
            except Exception:
                context['errmsg']="User Already Exists, Please Login...!"
                return render(request,'register.html',context)
        


def user_login(request):
    if request.method=='GET':
        return render(request,'login.html')
    else:
        n=request.POST['uname']
        p=request.POST['upass']
        #print(n)
        #print(p)
        u=authenticate(username=n,password=p)
        #print(u)
        if u is not None:
            login(request,u)
            return redirect('/product')
        else:
            context={}
            context['errmsg']='Invalid Username and Password'
            return render(request,'login.html',context)
        
def user_logout(request):
    logout(request)
    return redirect('/product')

def about(request):
    return redirect('/product')

def catfilter(request,cv):
    q1=Q(is_active=True)
    q2=Q(cat=cv)
    p=Product.objects.filter(q1 & q2)
    context={}
    context['data']=p
    return render(request,'index.html',context)


def sortbyprice(request,sv):
    #print(type(sv))
    if sv=='1':
        p=Product.objects.order_by('-price')
    else:
        p=Product.objects.order_by('price')

    context={}
    context['data']=p
    return render(request,'index.html',context)

def pricefilter(request):
    min=request.GET['min']
    max=request.GET['max']

    #print(min)
    #print(max)

    q1=Q(price__gte=min)
    q2=Q(price__lte=max)

    p=Product.objects.filter(q1 & q2)

    context={}
    context['data']=p
    return render(request,'index.html',context)

def search(request):
    query=request.GET['query']
    #print(query)
    pname=Product.objects.filter(name__icontains=query)
    pcat=Product.objects.filter(cat__icontains=query)
    pdetail=Product.objects.filter(pdetail__icontains=query)

    allprod=pname.union(pcat,pdetail)
    context={}
    
    if allprod.count()==0:
        context['errmsg']='Product NOT FOUND'

    context['data']=allprod
    return render(request,'index.html',context)

def productdetail(request,pid):
    p=Product.objects.filter(id=pid)
    context={}
    context['data']=p
    return render(request,'product_detail.html',context)

        
def addtocart(request,pid):
    if request.user.is_authenticated:
        #uid=request.user.id
        context={}
        u=User.objects.filter(id=request.user.id)
        p=Product.objects.filter(id=pid)
        #check product is exist or not
        q1=Q(uid=u[0])
        q2=Q(pid=p[0])
        c=Cart.objects.filter(q1 & q2)
        n=len(c)
        context['data']=p
        if n==1:
            context['errmsg']="Product Already Exist"
            return render(request,'product_detail.html',context)
        else:
            c=Cart.objects.create(uid=u[0],pid=p[0])
            c.save()
            context['msg']="Product added Successfully in the cart"
            return render(request,'product_detail.html',context)
            #return HttpResponse("Product added in cart")
    else:
        return redirect('/login')
    
def viewcart(request):
    c=Cart.objects.filter(uid=request.user.id)
    
    #print(c)

    context={}
    context['data']=c
    sum=0
    for x in c:
        sum=sum+x.pid.price*x.qty
    context['total']=sum
    context['n']=len(c)
    

    return render(request,'cart.html',context)

def updateqty(request,x,cid):
    c=Cart.objects.filter(id=cid)
    q=c[0].qty

    #print(type(x))
    if x =='1':
        q=q+1
    elif q>1:
        q=q-1
    c.update(qty=q)
    return redirect('/viewcart')
    return HttpResponse("Qty Fetched")

def remove(request,cid):
    c=Cart.objects.filter(id=cid)
    c.delete()
    return redirect('/viewcart')

def placeorder(request):
    c=Cart.objects.filter(uid=request.user.id)
    orderid=random.randrange(1000,9999)
    for x in c:
        amount=x.qty*x.pid.price
        o=Order.objects.create(orderid=orderid,pid=x.pid,uid=x.uid,qty=x.qty,amt=amount)
        o.save()

        x.delete()
    return redirect('/fetchorder')

def fetchorder(request):
    o=Order.objects.filter(uid=request.user.id)
    context={'data':o}
    sum=0
    for x in o:
        sum=sum+x.amt

    context['total']=sum
    context['n']=len(o)

    return render(request,'placeorder.html',context)


def makepayment(request):
    client = razorpay.Client(auth=("rzp_test_utsPyNSZqUkmq4", "pwiAlOcDCia2TnJqGsdgyhYA"))

    o=Order.objects.filter(uid=request.user.id)
    sum=0
    for x in o:
        sum=sum+x.amt
        oid=x.orderid

    data = { "amount": sum*100, "currency": "INR", "receipt": 'oid' }
    payment = client.order.create(data=data)
    #print(payment)
    context={}
    context['payment']=payment
    return render(request,'pay.html',context)

def paymentsuccess(request):
    sub='Handmade Crafts Order Status'
    msg='Thanks for shopping..!!'
    frm='sakshimahure56@gmail.com'
    u=User.objects.filter(id=request.user.id)
    to=u[0].email
    send_mail(
        sub,
        msg,
        frm,
        [to],
        fail_silently=False
    )

    return render(request,'paymentsuccess.html')