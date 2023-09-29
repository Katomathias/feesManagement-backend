from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework import status
from . serialisers import *
from . models import *
from django.db.models import Q  
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.auth import AuthToken
import random
import uuid 
from django.db.models import Sum
from django.http import JsonResponse
from django.db.models import Count
from rest_framework.authtoken.models import Token




@api_view(['GET'])
def homepage(request):
	res={
	"computers":"/computers"
}
	return Response(res, status.HTTP_200_OK)


@api_view(['GET'])
def stats_view(request, *args, **kwargs):
    users_count = User.objects.all().count()
    students_count = Students.objects.all().count()
    amount_collected = AmountPaid.objects.all().aggregate(Sum("amount"))
    response = {
        "user_count":users_count,
        "students_count":students_count,
        "amount_collected":amount_collected['amount__sum'] 
    }
    return Response(response, status=status.HTTP_200_OK)
@api_view(['POST'])
def login(request):
    serializer = AuthTokenSerializer( 
        data = request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    created, token = AuthToken.objects.create(user)
    return Response({
        'user_info':{
            'id':user.id,
            #'username':user.username,
            'email':user.email,
            'fullname':user.get_full_name()
        },
        'token':token
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def change_password(request, *args, **kwargs):
    data = request.data
    if data['id'] and data['password'] and data['old_password']:
        user = User.objects.get(id=data['id'])
        if user.check_password(data['old_password']):
            user.set_password(data['password'])
            user.save()
            msg = f"Hello {user.get_full_name()}, your password has been changed successfully!" 
        else:
            msg= "your old password is wrong"    
    else:
        msg = "please provide user id, old password and password"
    info = {"message":msg}
    return Response(info)

@api_view(['POST'])
def password_reset(request, *args, **kwargs):
    data = request.data
    if data['username']:
        try:
            user = User.objects.get(Q(username = data['username']) | Q(email=data['username']))
            random_no = random.randint(1000,9999)
            link = uuid.uuid4()
            PasswordResets.objects.update_or_create(
                user = user,
                code = random_no,
                link = link
            )
            msg = f"Hello {user.get_full_name()}, please check your email for link!" 
        except User.DoesNotExist:
            msg = f"no user found with username or email {data['username']}"
    else:
        msg = "please provide user id and password"
    info = {"message":msg}
    return Response(info)

@api_view(['POST'])       #for sending a link to user
def password_reset_done(request, *args, **kwargs):
    data = request.data
    if data['code'] and data['password']:
        try:
            user = PasswordResets.objects.get(code = data['code'])
            user = User.objects.get(id = user.user.id)
            user.set_password(data['password'])
            user.save()
            msg = f"Hello {user.get_full_name()}, your password has been changed successfully!" 
        except PasswordResets.DoesNotExist:
            msg = f"please provide a valid code"
    else:
        msg = "please provide a code and new password"
    info = {"message":msg}
    return Response(info)



@api_view(['GET','POST'])
def user_profiles(request, *args, **kwargs):
    if request.method == "GET":
        search = request.GET.get("search")
        all_profiles = Students.objects.all()
        if search:
            all_profiles = all_profiles.filter(name__icontains = search)
        serializer = StudentsSerializer(
            all_profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        data = request.data
        try:
            user = User.objects.create(
                first_name = data['first_name'],
                last_name = data['last_name'],
                username = data['username'],
                email = data['email']
            )
            user.set_password(data['password'])#rightly fully sets password
            user.save()
        except IntegrityError as e:
            msg = {
                "error":f"user with username {data['username']} exists",
                "additional_infomation":f"{e}"
            }
            return Response(msg)
        else:
            Students.objects.create(
                user = user,
                student_number = data['student_number'],
                dob = data['dob'],
                nationality = data['nationality'],
                gender = data['gender'],
                image = data['image']
            )
            return Response({"msg":"success register"}, 
                    status=status.HTTP_201_CREATED)
            
        
@api_view(['GET','POST'])
def user_profile_detail(request, slug):
    if request.method == "GET":
        try:
            selected_profile = UserProfile.objects.get(owner__id=slug)
        except UserProfile.DoesNotExist:
            return Response({"details":"No data found for specified id"}, status=status.HTTP_404_NOT_FOUND)
        details = {
            "full_name":selected_profile.owner.get_full_name(),
            "email":selected_profile.owner.email,
            "gender":selected_profile.gender,
            "dob":selected_profile.dob,
            "address":selected_profile.address,
            "contact":selected_profile.contact
        }
        return Response(details, status=status.HTTP_200_OK)
    else:
        data = request.data
        to_update = UserProfile.objects.get(owner=User.objects.get(id=slug))
        print(data)
        to_update.contact = data['tel']
        to_update.address = data['address']
        to_update.save()
        msg = {
            "message":"update successfull"
        }
        return Response(msg, status=status.HTTP_202_ACCEPTED)
    
@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({"error": "Please provide username, password, and email."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, email=email)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user_info': {
                'id': user.id,
                'email': user.email,
                'fullname': user.get_full_name()
            },
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
@api_view(['POST'])
def add_student(request):
    if request.method =='POST':
        student_name = request.data['name']
        student_number = request.data['student_number']
        student_nationality = request.data['nationality']
        student_gender = request.data['gender']
        student = Students(name=student_name, student_number=student_number, nationality=student_nationality, gender=student_gender)
        student.save()
        return JsonResponse({'success':True}) 
    
@api_view(['POST'])
def add_payment(request):
    if request.method == 'POST':
        name = request.data['name']
        amount = request.data['amount']
        level_name = request.data['level']  # Assuming you have 'level' field in your request data

        # Retrieve the student instance (replace student_id with actual value)
        student_instance = Students.objects.get(id=name)

        # Retrieve the level instance based on the level_name from request data
        level_instance = Levels.objects.get(name=level_name)

        # Create the AmountPaid instance with the correct student and level instances
        student_payment = AmountPaid(student=student_instance, level=level_instance, amount=amount)
        student_payment.save()

        return JsonResponse({'success': True})

    
@api_view(['DELETE'])
def delete_student(request, slug):
    if request.method == 'DELETE':
        student = Students.objects.get(id=slug)
        student.delete()
        return JsonResponse({'success':True})

@api_view(['GET','POST'])
def payments(request, *args, **kwargs):
    start_date = request.GET.get("start-date")
    end_date = request.GET.get("end-date")
    search = request.GET.get("name")
    if request.method == "GET":
        if kwargs:
            slug = kwargs['slug']
            payments =AmountPaid.objects.filter(
                student__id = slug
            )
            serializer = AllPaymentsSerializer(payments, many=True)
            return Response(serializer.data)
        if start_date and end_date:
            payments =AmountPaid.objects.filter(date__range = [start_date, end_date])
            returned = []
            for x in payments:
                returned.append({
                    "id": x.id,
                    "amount": x.amount,
                    "date": x.date,
                    "name": x.student.name,
                    "level": x.level.name,
                    "student_id":x.student.id,
                    "level_id":x.level.id
                })
            return Response(returned)
        if search:
            payments =AmountPaid.objects.filter(student__name__iexact = search)
            returned = []
            for x in payments:
                returned.append({
                    "id": x.id,
                    "amount": x.amount,
                    "date": x.date,
                    "name": x.student.name,
                    "level": x.level.name,
                    "student_id":x.student.id,
                    "level_id":x.level.id
                })
            return Response(returned)
        serializer = AllPaymentsSerializer.all_students()
        return Response(serializer)
    else:
        serialiser = AllPaymentsSerializer(
            data=request.data
        )
        if serialiser.is_valid():
            serialiser.save()
            return Response({"msg":"data saved"}, status=status.HTTP_201_CREATED)
        return Response(serialiser.errors, status=status.HTTP_404_NOT_FOUND)

#for one item
@api_view(['GET', 'PUT', 'DELETE'])
def payment_detail(request, slug):
    try:
        payment_effected = AmountPaid.objects.get(pk=slug)
    except AmountPaid.DoesNotExist:
        return Response({"details":"No data found for specified id"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AllPaymentsSerializer(payment_effected)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = AllPaymentsSerializer(payment_effected, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        payment_effected.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    
    #Views for Graphs are under here
    
def get_item_count(request):
    male_no = Students.objects.filter(gender='MALE').count()
    male_no=int(male_no)
    female_no = Students.objects.filter(gender='FEMALE').count()
    female_no=int(female_no)
    gender_list= ['MALE', 'FEMALE']
    gender_number=[male_no, female_no]
    context={' gender_list': gender_list, 'gender_number':gender_number}
    return JsonResponse({'male_no':  male_no,'female_no':  female_no, ' gender_list': gender_list, 'gender_number':gender_number })

def get_nationality_counts(request):
    nationality_counts = Students.objects.values('nationality').annotate(count=Count('id'))
    data = {
        'nationalities': [entry['nationality'] for entry in nationality_counts],
        'counts': [entry['count'] for entry in nationality_counts],
    }
    return JsonResponse(data)

def get_amount_by_levels(request):
    amount_by_levels = AmountPaid.objects.values('level__name').annotate(total_amount=Sum('amount'))
    data = {
        'levels': [entry['level__name'] for entry in amount_by_levels],
        'amounts': [entry['total_amount'] for entry in amount_by_levels],
    }
    return JsonResponse(data)
    


# Create your views here.

"""
def studentsView(request):
    male_no=UserProfile.objects.filter(gender='MALE').count()
    male_no=int(male_no)
    print('Number of male students is', male_no)
    
    female_no=UserProfile.objects.filter(gender='FEMALE').count()
    female_no=int(female_no)
    print('Number of female students is', female_no)
    
    gender_list= ['MALE', 'FEMALE']
    gender_number=[male_no, female_no]
    
    context={' gender_list': gender_list, 'gender_number':gender_number}
    return render(request,context)
    
@api_view(['GET'])
def homepage(request):
	res={
	"computers":"/computers"
}
	return Response(res, status.HTTP_200_OK)
@api_view(['GET','POST'])
def computers(request):
    if request.method=='GET':
        #adding a seaarch filter
        search = request.GET.get("search")
        start_p=request.GET.get("start_p")
        end_p=request.GET.get("end_p")
        start_date=request.GET.get("start_date")
        end_date=request.GET.get("end_end")
        all_pcs = Computers.objects.all()
        if search:
            #exact gets the exact name and is case-sensitive unlike iexact
            #all_pcs=all_pcs.filter(name__iexact=name)
            #and contains is case-sensitive unlike icontains but
            #returns something that has the characters entered in search
            all_pcs=all_pcs.filter(Q(name__iexact=search) | Q(model__iexact=search))
        if start_p and end_p:
            all_pcs=all_pcs.filter(
                price__range=[start_p, end_p]
            
            )
        if start_date and end_date:
            all_pcs=all_pcs.filter(
                created_at__date__range=[start_date, end_date]
            
            )
        serializer = ComputerSerialiser(
        all_pcs, many=True)
        return Response(
        serializer.data, status=status.HTTP_200_OK)
        
    #for POST method below
    else:
        data=request.data
        serializer=ComputerSerialiser(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
  
@api_view(['GET', 'PUT', 'DELETE']) 
def computer_detail(request, slug):
    try:
        pc_obtained = Computers.objects.get(pk=slug)
    except Computers.DoesNotExist:
        return Response(
            {"details":"No computer found"}, 
            status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ComputerSerialiser(pc_obtained)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = ComputerSerialiser(
            pc_obtained, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_202_ACCEPTED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        pc_obtained.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        """
        
"""
        @api_view(['GET','POST'])
def payments(request, *args, **kwargs):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if request.method == "GET":
        if kwargs:
            slug = kwargs['slug']
            payments =AmountPaid.objects.filter(
                student__id = slug
            )
            serializer = AllPaymentsSerializer(payments, many=True)
            return Response(serializer.data)
        else:
            if start_date and end_date:
                
                payments =AmountPaid.objects.filter(
                    date__range = [start_date, end_date])
                serializer = AllPaymentsSerializer(payments, many=True)
                return Response(serializer.data)
                
            else:
                payments =AmountPaid.objects.all()
        #      serializer = AllPaymentsSerializer.all_students()
        serializer = AllPaymentsSerializer(payments, many=True)  
        return Response(serializer.data)
    else:
        serialiser = AllPaymentsSerializer(
            data=request.data
        )
        if serialiser.is_valid():
            serialiser.save()
            return Response({"msg":"data saved"}, status=status.HTTP_201_CREATED)
        return Response(serialiser.errors, status=status.HTTP_404_NOT_FOUND)
    """