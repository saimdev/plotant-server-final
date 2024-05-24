from account.jwt import decode_jwt_token, generate_jwt_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view #type: ignore
from rest_framework.response import Response #type: ignore
from project import file_operations
from .models import User





@csrf_exempt
@api_view(['POST'])
def Authentication(request):
    token = request.COOKIES.get('token')
    if token:
        try:
            JWT_str = decode_jwt_token(token)
            return Response({'message': 'Success','userName': JWT_str['user'], 'email':JWT_str['email']})
        except Exception as e:
            return Response({'error': 'Invalid token'})
    else:
        return Response({'error': 'Token not found in cookies'})
    
@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        existing_user = User.objects.filter(
            email=request.data.get('email')).first()
        if existing_user is None:

            user = User(username=request.data.get('name'), email=request.data.get(
                'email'), password=request.data.get('password'))

            file_operations.create(user.email)
            
            user.save()
            return Response({'message': 'Successfully Registered'})
        else:
            return Response({'error': 'User with the same email already exists'})
    else:
        return Response({'error': 'Something went wrong'})


@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        print(email, password)
        user = User.objects.filter(email=email).first()

        if user is None:
            return Response({'error': 'User does not exist'})
        
        print(user.email)
        if user.password == password:
            JWT = generate_jwt_token(user.username, user.email, user.id)

            response = Response({'success': 'Login Successfull.'})
            response.set_cookie('token', JWT, max_age=36000) 
            return response
        else:
            return Response({'error': 'Incorrect password'})
    else:
        return Response({'error': 'Method not allowed'})
    
@api_view(['GET'])
def logout(request):
    if request.method == 'GET':
        token = request.COOKIES.get('token')
        try:
            user = decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        if token:
            response = Response({'message': 'Success'})
            response.delete_cookie('token')

            return response
        else:
            return Response({'error': 'Token not found in cookies'})
    else:
        return Response({'error': 'Method not allowed'})
    

@api_view(['POST'])
def updateProfile(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        try:
            user = decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        name = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if password is None:
            user = User.objects.get(email=email)
            user.username = name
            user.email = email
            user.save()

            return Response({'message': 'Successfully Updated'})
        else:
            user = User.objects.get(email=email)
            user.username = name
            user.email = email
            user.password = password
            user.save()

            return Response({'message': 'Successfully Updated'})
    else:
        return Response({'error': 'Something went wrong'})