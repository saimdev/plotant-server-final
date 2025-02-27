from .models import User, Project,  Associate, File, Trash, Archived, Notification, GraphData, Logs
from project.file_operations import ProjectProcessor, DataProcessor
from project.databaseOperations import logsData, Graph, oneData, updateData
from django.db.models.functions import TruncMonth, Concat
from django.db.models import Count, F, IntegerField
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.decorators import api_view  # type: ignore
from rest_framework.response import Response  # type: ignore
from django.utils.html import strip_tags
from django.forms import model_to_dict
from django.shortcuts import redirect
from django.http import FileResponse
from django.conf import settings
from account import jwt
import datetime
import json
import os


data_processor = DataProcessor()
project_processor = ProjectProcessor()




@api_view(['GET'])
def sendMail(request):
    sub,to = 'PlotAnt Notification', ['malik.hassan5499@gmail.com']
    html_message = render_to_string('notification.html', {'id': 4}) 
    plain_message = strip_tags(html_message)  
    email = EmailMultiAlternatives(
      subject=sub,
      body=plain_message,  
      from_email=settings.EMAIL_HOST_USER,  
      to=to,
    )
    email.attach_alternative(html_message, 'text/html')  

    try:
        email.send()
        return Response({'success': True})
    except Exception as e:
        print(f"Error sending email: {e}")
        return Response({'success': False})


@api_view(['POST'])
def createProject(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        project_name = request.data.get('projectname')
        file = request.FILES.get('file')

        
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        if not file.name.endswith('.csv'):
            return Response({'error': 'invalid format'}, status=400)
        
        res = project_processor.checknan(file)
        if res != 1:
            return Response(res, status=400)

        checkProject = Project.objects.filter(user_id=user['user_id'], name=project_name).first()
        if checkProject:
            return Response({'error': 'Project already exists.'}, status=400)
        
        new_project = Project(name=project_name, date=datetime.datetime.now(), user_id=user['user_id'])
        new_project.save()

        new_file = File(name=file.name, project_id=new_project.id,date=datetime.datetime.now(), modified_date=datetime.datetime.now())
        new_file.save()

        project_role = Associate(role='owner', project_id=new_project.id,user_id=user['user_id'], date=datetime.datetime.now())
        project_role.save()
        data = project_processor.create_project(user['email'], project_name, file)

        log = {
                'project_id': new_project.id,
                'file_id': new_file.id,
            }
        logsData(project_role.role, f'Created {file.name} file', **log)
        

        return Response({'message': data['message']}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def projectCount(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        try:
            count = Associate.objects.filter(user_id=user['user_id'], role='owner').count()
            latest_project = Associate.objects.filter(user_id=user['user_id'], role='owner').annotate(year_month_day=Concat(
                F('date__year'), F('date__month'), F('date__day'), output_field=IntegerField())).order_by('-year_month_day')
            latestProject = latest_project[0].date.strftime('%Y-%m-%d') if latest_project else None
        except:
            count = 0
            latestProject = None

        try:
            sharedcount = Associate.objects.filter(user_id=user['user_id']).exclude(role='owner').count()
            latest_shared_project = Associate.objects.filter(user_id=user['user_id']).exclude(role='owner').annotate(year_month_day=Concat(F('date__year'), F('date__month'), F('date__day'), output_field=IntegerField())).order_by('-year_month_day')
            latestSharedProject = latest_shared_project[0].date.strftime('%Y-%m-%d') if latest_shared_project else None
        except:
            sharedcount = 0
            latestSharedProject = None

        return Response({'message': 'Project List', 'projectsCount': count, 'latestProject': latestProject, 'sharedCount': sharedcount, 'latestSharedProject': latestSharedProject})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def projectGraphCount(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)


        month_project_counts = {str(i).zfill(2): 0 for i in range(1, 13)}
        your_month_project_counts = {str(i).zfill(2): 0 for i in range(1, 13)}
        shared_month_project_counts = {
            str(i).zfill(2): 0 for i in range(1, 13)
            }

        projects_by_month = Associate.objects.filter(user_id=user['user_id']) \
            .annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(count=Count('project')) \
            .order_by('month')

        projects_count_list = list(projects_by_month)
        for item in projects_count_list:
            month = item['month'].strftime('%m')
            count = item['count']
            month_project_counts[month] = count
        # ========================================

        your_projects_by_month = Associate.objects.filter(user_id=user['user_id'], role='owner') \
            .annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(count=Count('project')) \
            .order_by('month')

        your_projects_count_list = list(your_projects_by_month)
        for item in your_projects_count_list:
            month = item['month'].strftime('%m')
            count = item['count']
            your_month_project_counts[month] = count
        # ==============================================

        shared_projects_by_month = Associate.objects.filter(user_id=user['user_id']).exclude(role='owner') \
            .annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(count=Count('project')) \
            .order_by('month')

        shared_projects_count_list = list(shared_projects_by_month)
        for item in shared_projects_count_list:
            month = item['month'].strftime('%m')
            count = item['count']
            shared_month_project_counts[month] = count

        return Response({'message': 'Project List by Month', 'projectsCountByMonth': month_project_counts, 'yourProjectsCountByMonth': your_month_project_counts, 'sharedProjectsCountByMonth': shared_month_project_counts})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def projectList(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        projects = Associate.objects.filter(user_id=user['user_id']).select_related('project').values('project__id', 'project__name', 'role', 'date','project__user__username')
        data = []
        for p in projects:
            data.append({
                'project__id': p['project__id'],
                'project__name': p['project__name'],
                'role': p['role'],
                'date': p['date'],
                'project_username': p['project__user__username']
                })



        return Response({'message': 'Project List', 'projects': data})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def yourProjects(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        user = jwt.decode_jwt_token(token)
        projects = Associate.objects.filter(user_id=user['user_id'], role='owner').select_related(
            'project').values('project__id', 'project__name', 'project__date', 'role', 'date')

        return Response({'message': 'Project List', 'projects': projects})
    else:
        return Response({'error': 'Invalid request method'}, status=400)



# ======================== PROJECT SHARING =========================
# ==================================================================

@api_view(['POST'])
def sendNotification(request):
    if request.method == "POST":
        shareWith = request.data.get('userEmail')
        projectId = request.data.get('projectId')
        accessType = request.data.get('accessType')

        token = request.COOKIES.get('token')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        ownerCheck = Associate.objects.get(user_id=user['user_id'], project_id=projectId, role='owner')
        if not ownerCheck:
            return Response({'error': 'You are not the owner of this project.'}, status=400)
        
        if user['email'] == shareWith:
            return Response({'error': 'You cannot assign role to yourself.'}, status=400)

        try:
            su = User.objects.get(email=shareWith)
        except:
            return Response({'error': 'user not exists.'}, status=400)
        

        notification = Notification(project_id=projectId, sender_id=user['user_id'], receiver_id=su.id, role=accessType, read=0, toast=0, date=datetime.datetime.now(), message= f"{user['user']} has sent you a {accessType} access for the project {ownerCheck.project.name}.")
        check = Associate.objects.filter(user_id=notification.receiver_id, project_id=projectId).first()
        if check:
            if check.role == notification.role:
                return Response({'message': f'The user has been already granted the {accessType} role.'})


        notification.save()
        # sub,to = 'PlotAnt Notification', [notification.receiver.email]
        # html_message = render_to_string('notification.html', {'id': notification.id, 'sender': notification.sender.username, 'reciever':notification.receiver.username, 'accessType': accessType, 'project':notification.project.name, 'date':notification.date}) 
        # plain_message = strip_tags(html_message)  
        # email = EmailMultiAlternatives(
        # subject=sub,
        # body=plain_message,  
        # from_email=settings.EMAIL_HOST_USER,  
        # to=to,
        # )
        # email.attach_alternative(html_message, 'text/html')
        # email.send()

        return Response({'message': f'The user has been granted the {accessType} role.'})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def openNotification(request):
    token = request.COOKIES.get('token')
    notificationId = request.data.get('id')

    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    notification = Notification.objects.get(id=notificationId)
    notification.read = 1
    notification.save()

    sharer = User.objects.get(id=notification.sender_id)
    project = Project.objects.get(id=notification.project_id) 

    sharerInfo = {
        'username': notification.sender.username,
        'email': notification.sender.email,
        'project': project.name,
        'accessType': notification.role,
        'previous': notification.pre_accept,
        'date': notification.date
    }
    return Response({'message':'Sussessfully.','sharerInfo': sharerInfo}, status=200)


def testNotification(request, id):
    return redirect("http://192.168.1.115:3000/analysis/readNotification")


@api_view(['POST'])
def markAsRead(request):
    notificationId = request.data.get('id')

    token = request.COOKIES.get('token')
    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    notification = Notification.objects.get(id=notificationId)
    notification.read = 1
    notification.save()

    return Response({'message':'Sussessfull.'}, status=200)


@api_view(['GET'])
def markAllAsRead(request):
    token = request.COOKIES.get('token')
    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    notification = Notification.objects.filter(receiver_id=user['user_id'])
    for n in notification:
        n.read = 1
        n.save()

    return Response({'message':'Sussessfull.'}, status=200)


@api_view(['POST'])
def shareAccept(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        notification = request.data.get('id')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        notification = Notification.objects.get(id=notification)
        
        notification.read = 1
        notification.acceptance = 1
        notification.save()

        associate = Associate(role=notification.role, project_id=notification.project_id,user_id=notification.receiver_id, date=datetime.datetime.now())
        associate.save()

        notification1 = Notification(
            project_id=notification.project_id, 
            sender_id=notification.receiver_id, 
            receiver_id=notification.sender_id, 
            role=notification.role, 
            pre_accept=notification.acceptance, 
            message=f'{notification.receiver.username} has accepted your request against project {notification.project.name}', 
            read=0, 
            toast=0, 
            acceptance=3,
            date=datetime.datetime.now())
        notification1.save()

        return Response({'message': 'Accepted successfully.'})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def shareDecline(request):
    token = request.COOKIES.get('token')
    notificationId = request.data.get('id')

    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    notification = Notification.objects.get(id=notificationId)
    notification.read = 1
    notification.acceptance = 2
    notification.save()

    notification1 = Notification(
            project_id=notification.project_id, 
            sender_id=notification.receiver_id, 
            receiver_id=notification.sender_id, 
            role=notification.role, 
            pre_accept=notification.acceptance,
            message=f'{notification.receiver.username} has declined your request against project {notification.project.name}', 
            read=0, 
            toast=0, 
            acceptance=3,
            date=datetime.datetime.now())
    notification1.save()

    return Response({'message': 'successfull'}, status=200)


@api_view(['GET'])
def sharedProjects(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        associate = Associate.objects.filter(user_id=user['user_id']).exclude(
            role='owner').select_related('project').values('project__id', 'project__name', 'role', 'date')

        projects = []
        for item in associate:
            owner = Associate.objects.filter(
                project_id=item['project__id'], role='owner').first()
            on = User.objects.get(id=owner.user_id)
            project_info = {
                'project_id': item['project__id'],
                'project_name': item['project__name'],
                'role': item['role'],
                'date': item['date'],
                'owner': on.username
            }
            projects.append(project_info)

        return Response({'message': 'Project List', 'projects': projects})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def getNotifications(request):
    token = request.COOKIES.get('token')

    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    toaster_notifications = Notification.objects.filter(receiver_id=user['user_id'], toast=0) 
    bell_notifications = Notification.objects.filter(receiver_id=user['user_id'])


    for t in toaster_notifications:
        print(f'\n\n{t.sender.username}\n\n')
    toast_data = []
    for notification in toaster_notifications:
        notification.toast = 1
        toast_data.append({
            'message': notification.message
        })
        notification.save()

    bell_data = []
    unread_count = 0
    for notification1 in bell_notifications:
        if notification1.read == '0':
            print(notification1.read)
            unread_count = unread_count + 1
        bell_data.append({
            'message': notification1.message,
            'status': notification1.read, 
            'id': notification1.id,
            'date': notification1.date,
            'acceptance': notification1.acceptance
        })

    return Response({'toaster': toast_data, 'bell': bell_data, 'unread_count': unread_count})


@api_view(['POSt'])
def deleteNotification(request):
    token = request.COOKIES.get('token')
    notificationId = request.data.get('id')

    try:
        user = jwt.decode_jwt_token(token)
    except:
        return Response({'error': 'Invalid token'}, status=401)

    notification = Notification.objects.get(id=notificationId)
    notification.delete()

    return Response({'message':'Deleteed Sussessfull.'}, status=200)

# -------------------------------------------------------------------



# ================== PROJECT (OPEN - DOWNLOAD) =====================
# ==================================================================

@api_view(['POST'])
def projectOpen(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectid = request.data.get('projectId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        file = File.objects.filter(project_id=projectid)
        associate = Associate.objects.get(project_id=projectid, user_id=user['user_id'])

        file_objects = []

        for f in file:
            file_object = {
                'project_name': f.project.name,
                'id': f.id,
                'name': f.name,
                'access_type': associate.role,
            }
            file_objects.append(file_object)
        
        return Response({'files': file_objects, 'message': 'List of All files.'}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)
    

@api_view(['POST'])
def download_project_file(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        project_id = request.data.get('projectID')
        project = Project.objects.get(id=project_id)

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        associate = Associate.objects.get(user_id=user['user_id'], project_id=project_id)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)
        
        file_path = project_processor.downloadFile(user['email'], project.name)
        try:
            if os.path.exists(file_path):
                return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=f'{associate.project.name}.zip')
        except Exception as e:
            return Response({'error': 'An error occurred during download'}, status=500)
        finally:
            project_processor.delete_downloaded_file(file_path)
    else:
        return Response({'error': 'Invalid request method'}, status=400)
    
# -------------------------------------------------------------------




# ======================== PROJECT ARCHIVE =========================
# ==================================================================
@api_view(['POST'])
def archiveProject(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectId = request.data.get('projectId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        project = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        archive = Archived(role=project.role, project_id=project.project_id,user_id=project.user_id, date=project.date)
        archive.save()
        project.delete()
        return Response({'message': f'The Project has been archived successfully.'})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def unArchive(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectId = request.data.get('projectId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        archive = Archived.objects.get(
            user_id=user['user_id'], project_id=projectId)
        associate = Associate(role=archive.role, project_id=archive.project_id,user_id=archive.user_id, date=archive.date)
        associate.save()
        archive.delete()
        return Response({'message': f'The Project has been unarchived successfully.'})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['GET'])
def archivedProjects(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        archive = Archived.objects.filter(user_id=user['user_id']).select_related(
            'project').values('project__id', 'project__name', 'role', 'date')

        return Response({'message': 'Project List', 'projects': archive})
    else:
        return Response({'error': 'Invalid request method'}, status=400)

# -------------------------------------------------------------------



# ====================== PROJECT TRASH & DELETE=====================
# ==================================================================
@api_view(['GET'])
def trashedProject(request):
    if request.method == "GET":
        token = request.COOKIES.get('token')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        trash = Trash.objects.filter(user_id=user['user_id']).values('id', 'project', 'projectcreatedate', 'date')

        return Response({'message': 'Project List', 'trash': list(trash)})
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def projectDelete(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        project_id = request.data.get('projectID')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        

        associate = Associate.objects.get(project_id=project_id, user_id=user['user_id'])
        right = associate.role
        if associate.role != 'owner':
            associate.delete()
            return Response({'error': f'You {right} right has been removed.'}, status=400)

        project = Project.objects.get(id=project_id)

        u = User.objects.get(id=user['user_id'])

        files = File.objects.filter(project_id=project_id)

        filenames = ', '.join([file.name for file in files])
        filecreatedate = ', '.join([file.date.strftime('%Y-%m-%d %H:%M:%S') for file in files])
        modifydate = ', '.join([file.modified_date.strftime('%Y-%m-%d %H:%M:%S') if file.modified_date else '' for file in files])

        project_processor.delete_project(user['email'], project.name)
        trash_obj = Trash(
            user_id=u.id,
            project=project.name,
            filename=filenames,
            date=datetime.datetime.now(),
            filecreatedate=filecreatedate,
            modifydate=modifydate,
            projectcreatedate=project.date.strftime('%Y-%m-%d %H:%M:%S')
        )
        trash_obj.save()
        associate.delete()
        project.delete()
        files.delete()

        return Response({'message': 'Project deleted successfully.'}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def projectRestore(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        trash_id = request.data.get('trashId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        trash = Trash.objects.get(id=trash_id)

        project_processor.restore_project(user['email'], trash.project)

        project = Project(name=trash.project,date=trash.projectcreatedate, user_id=user['user_id'])
        project.save()
        associate = Associate(role='owner', date=trash.projectcreatedate,project_id=project.id, user_id=user['user_id'])
        associate.save()
        filenames = trash.filename.split(', ')
        filecreatedates = trash.filecreatedate.split(', ')
        modifydates = trash.modifydate.split(', ')

        for filename, filecreatedate, modifydate in zip(filenames, filecreatedates, modifydates):
            filecreatedate_obj = datetime.datetime.strptime(
                filecreatedate, '%Y-%m-%d %H:%M:%S')
            modifydate_obj = datetime.datetime.strptime(
                modifydate, '%Y-%m-%d %H:%M:%S') if modifydate else None

            file = File(name=filename, date=filecreatedate_obj,modified_date=modifydate_obj, project_id=project.id)
            file.save()
        trash.delete()
        
        return Response({'message': 'Project Restored successfully.'}, status=200)
    

@api_view(['POST'])
def projectDeletePermanently(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        trash_id = request.data.get('trashId')

        print(trash_id)

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        trash = Trash.objects.get(id=trash_id)

        res = project_processor.delete_project_permanent(user['email'], trash.project)

        trash.delete()

        return Response({'message': res}, status=200)
    
# -------------------------------------------------------------------



# ================== FILE (DELETE - RENAME) ========================
# ==================================================================
@api_view(['POST'])
def fileDelete(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)


        try:
            project = Project.objects.get(id=projectId)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=404)

        try:
            file = File.objects.get(id=fileId, project_id=projectId)
        except File.DoesNotExist:
            return Response({'error': 'File not found.'}, status=404)

        project_processor.delete_file(user['email'], project.name, file.name)
        file.delete()

        return Response({'message': 'File deleted successfully.'}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def fileRename(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')
        fileName = request.data.get('fileName')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        # access right check
        associate = Associate.objects.get(user_id=user['user_id'],project_id=projectId)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)

        # project check 
        try:
            project = Project.objects.get(id=projectId)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=404)

        try:
            file = File.objects.get(id=fileId, project_id=projectId)
        except File.DoesNotExist:
            return Response({'error': 'File not found.'}, status=404)

        data = project_processor.rename_file(user['email'], project.name, file.name, fileName)
        previousFileName = file.name
        file.name = fileName+'.csv'
        file.save()

        graph = GraphData.objects.get(file_id=fileId).exclude('collaborator','message')
        if graph:
            logsData(project.role, f'file Renamed from {previousFileName} to {fileName}.', **graph)
        else:   
            log = {
                'user_id': user['user_id'],
                'project_id': projectId,
                'file_id': fileId,
                }
            logsData(project.role, f'file Renamed from {previousFileName} to {fileName}.', **log)

        return Response({'message': data['message']}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)


@api_view(['POST'])
def newFile(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectid = request.data.get('projectname')
        file = request.FILES.get('file')
        overWrite = request.data.get('overWrite')
        
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        if not file.name.endswith('.csv'):
            return Response({'error': 'invalid format'}, status=400)
        
        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectid)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)
        nf = 0
        if overWrite == '0':
            new_file = File(name=file.name, project_id=projectid, date=datetime.datetime.now(), modified_date=datetime.datetime.now())
            new_file.save()
            nf = new_file.id

        data = project_processor.save_file(user['email'], associate.project.name, file)

        log = {
                'project_id': projectid,
                'file_id': nf,
            }
        logsData(associate.role, f'Created {file.name} file', **log)

        return Response({'message': 'File Uploaded successfully.', 'check': True}, status=200)
    else:
        return Response({'error': 'Invalid request method'}, status=400)

# -------------------------------------------------------------------


 
# ======================== DATA OPERATIONS =========================
# ==================================================================

@api_view(['POST'])
def analyse(request):
    if request.method == "POST":
        token = request.COOKIES.get('token')
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        project = Project.objects.get(id=projectId)
        file = File.objects.get(id=fileId)
        
        # check role 
        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role == 'read':
            owner = Associate.objects.get(project_id=projectId, role='owner')
            userEmail = owner.user.email
            accessType = 'read'
        elif associate.role =='write':
            owner = Associate.objects.get(project_id=projectId, role='owner')
            userEmail = owner.user.email
            accessType = 'write'
        else:
            userEmail = user['email']
            accessType = 'write'
        
        data = data_processor.open_file(userEmail, project.name, file.name)

        return Response({
                    'data': data['head'],
                    'columns': data['column_names'],
                    'columns_data': data['column_data'],
                    'columns_unique_data': data['column_data_unique'],
                    'type': data['type'],
                    'access_type': accessType, 
                }, status=200)

    else:
        return Response({'error': 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def labels(request):
    if request.method == 'POST':
        flg = False
        c = ''
        float_condition = 0.0
        token = request.COOKIES.get('token')
        x = request.data.get('x_label')
        y = request.data.get('y_label')
        condition = request.data.get('condition')
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        

        # role check 
        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)

        if associate.role =='write':
            owner = Associate.objects.get(project_id=projectId, role='owner')
            userEmail = owner.user.email
        else:
            userEmail = user['email']

        project = Project.objects.get(id=projectId)
        file = File.objects.get(id=fileId)

        if condition is not None:
            try:
                parsed_condition = json.loads(condition)
                if type(parsed_condition) is int:
                    float_condition = float(parsed_condition)
                    flg = 'float'

                if type(parsed_condition) is float:
                    float_condition = float(parsed_condition)
                    flg = 'float'
            except:
                flg = 'test'
                c = condition

        print('\n', x, ' , ', y, ' , ', condition,' , ', file.name, ' ', project.name, '\n', 'here')

        if flg == 'float':
            labels = data_processor.get_labels(userEmail, x, y, float_condition, file.name)
        elif flg == 'test':
            labels = data_processor.get_labels(userEmail, x, y, c, file.name)
        else:
            labels = data_processor.get_labels(userEmail, x, y, project.name, file.name)
        labels = json.loads(labels)

        print('\n', labels, '\n')

        return Response({'labels': labels,}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def labels_legends(request):
    if request.method == 'POST':
        x = request.data.get('x_label')
        y = request.data.get('y_label')
        z = request.data.get('z')
        token = request.COOKIES.get('token')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')

        project = Project.objects.get(id=projectId)
        file = File.objects.get(id=fileId)

        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)


        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role =='write':
            owner = Associate.objects.get(project_id=projectId, role='owner')
            userEmail = owner.user.email
        else:
            userEmail = user['email']


        print('\n', x, ' , ', y, ' , ', z,  ' , ',project.name, ' , ', file.name, '\n')

        labels = data_processor.get_labels_legends(userEmail, x, y[0], z, project.name, file.name)

        labels = json.loads(labels)

        print('\n', labels, '\n')

        return Response({'labels':labels}, status=200)
        return Response({
            'x': labels['x'],
            'y': labels['y'],
            'z': labels['z'],
        }, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def edit_value(request):
    if request.method == 'POST':
        rowIndex = request.data.get('rowIndex')
        columnIndex = request.data.get('columnIndex')
        columnkey = request.data.get('columnKey')
        xLabel = request.data.get('xLabel')
        yLabel = request.data.get('yLabel')
        value = request.data.get('value')
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')

        token = request.COOKIES.get('token')

        print(xLabel, yLabel)
        
        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)

        project = Project.objects.get(id=projectId)
        file = File.objects.get(id=fileId)

        # role check 
        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)

        if associate.role =='write':
            owner = Associate.objects.get(project_id=projectId, role='owner')
            userEmail = owner.user.email
        else:
            userEmail = user['email']
        

        print(f'\n{userEmail} - {rowIndex} - {columnkey} - {value} - {xLabel} - {yLabel} - {project.name} {file.name}')


        result =  data_processor.edit_val(userEmail, rowIndex, columnkey,  value, xLabel, yLabel,project.name, file.name )
        labels = json.loads(result)
        return Response({'labels': labels}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def saveGraph(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        projectId = request.data.get('project_id')
        fileId = request.data.get('file_id')
        currentGraphId = request.data.get('currentGraphId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        data = request.data
        data['user_id'] = user['user_id']

        # if GraphData.objects.filter(id=currentGraphId).exists():
        #     g = GraphData.objects.get(id=currentGraphId)
        #     updateData(g.id, **data)
        #     return Response({'message': 'Graph data saved successfully'}, status=201)

        associate = Associate.objects.get(user_id=user['user_id'], project_id=projectId)

        if Graph(associate.role, data.get('graphName'), **data):
            return Response({'message': 'Graph data saved successfully'}, status=201)
        else:
            
            return Response({'error': 'Failed to save graph data'}, status=400)
        
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def getGraph(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        
        projectId = request.data.get('projectId')
        
        fileId = request.data.get('fileId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        associate = Associate.objects.get(project_id=projectId, role='owner')
        
        graphData= GraphData.objects.filter(project_id=projectId, file_id=fileId, user_id=associate.user_id)
        if not graphData.exists():
            return Response({'message': 'Graph Data.', 'data':None}, status=200)
        
        serialized_data = [model_to_dict(graph) for graph in graphData]

        return Response({'message': 'Graph Data.', 'data': serialized_data}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)
    
    
@api_view(['POST'])
def getLogsGraph(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        
        logId = request.data.get('logId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        graphData = Logs.objects.get(id=logId)
        serialized_data = model_to_dict(graphData)
        oneData(**serialized_data)

        return Response({'message': 'Graph Data.', 'data': serialized_data}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)
    # if request.method == 'POST':
    #     token = request.COOKIES.get('token')
    #     logId = request.data.get('logId')

    #     try:
    #         user = jwt.decode_jwt_token(token)
    #     except:
    #         return Response({'error': 'Invalid token'}, status=401)

    #     log = Logs.objects.get(id=logId)

    #     u = User.objects.get(id=user['user_id'])

        # if not GraphData.objects.get(id=log.graph_id).exist():
        #     graph_data = GraphData.objects.create(
        #     user=u,
        #     project_id=log.project_id,
        #     file_id=log.file_id,
        #     graphName=log.graphName,
        #     xAxis=log.xAxis,
        #     yAxis=log.yAxis,
        #     parameters=log.parameters,
        #     barColors=log.barColors,
        #     selectedLabels=log.selectedLabels,
        #     xLabelColor=log.xLabelColor,
        #     yLabelColor=log.yLabelColor,
        #     graphHeadSize=log.graphHeadSize,
        #     graphHeadWeight=log.graphHeadWeight,
        #     xLabelSize=log.xLabelSize,
        #     xLabelWeight=log.xLabelWeight,
        #     yLabelSize=log.yLabelSize,
        #     yLabelWeight=log.yLabelWeight,
        #     graphHeading=log.graphHeading,
        #     barBorders=log.barBorders,
        #     condition=log.condition,
        #     conditionalParameters=log.conditionalParameters,
        #     yAxisConditions=log.yAxisConditions,
        #     yAxisValue=log.yAxisValue,
        #     textureColor=log.textureColor,
        #     textureBg=log.textureBg,
        #     legends=log.legends,
        #     reference=log.reference,
        #     colorStatesTexture=log.colorStatesTexture,
        #     colorStatesBgTexture=log.colorStatesBgTexture,
        #     dictionaryState=log.dictionaryState,
        #     borderColor=log.borderColor,
        #     dlSize=log.dlSize,
        #     dlWeight=log.dlWeight,
        #     dlColor=log.dlColor,
        #     stepped=log.stepped,
        #     dataLabelsConfig=log.dataLabelsConfig,
        #     fontFamily=log.fontFamily,
        #     stepSize=log.stepSize,
        #     legendPosition=log.legendPosition,
        #     greyShadeCheck=log.greyShadeCheck,
        # )


    #     serialized_data = model_to_dict(log)

    #     return Response({'message': 'Graph Data.', 'data': serialized_data}, status=200)
    # else:
    #     return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def deleteGraph(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        graphId = request.data.get('graphId')

        print(graphId)

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        graph_data = GraphData.objects.get(id=graphId)
        
        associate = Associate.objects.get(user_id=user['user_id'], project_id=graph_data.project_id)
        if associate.role == 'read':
            return Response({'error': 'You do not have the right to perform this action.'}, status=400)
        
        # delGraph = GraphData.objects.get(id=graphId)
        graph_data.delete()

        return Response({'message': 'Graph Deleted Successfully.'}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)


@api_view(['POST'])
def projectHistory(request):
    if request.method == 'POST':
        token = request.COOKIES.get('token')
        
        projectId = request.data.get('projectId')
        fileId = request.data.get('fileId')

        try:
            user = jwt.decode_jwt_token(token)
        except:
            return Response({'error': 'Invalid token'}, status=401)
        
        graphData = Logs.objects.filter(project_id=projectId, file_id=fileId)

        if not graphData.exists():
            return Response({'message': 'Graph Data.', 'data':None}, status=200)

        data_list = []
        for data in graphData:
            graphUser = User.objects.get(id=data.user_id)
            formatted_time = data.date.strftime("%I:%M %p")

            data_entry = {
                'userId': data.user_id,
                'userName': graphUser.username,
                'logId': data.id,
                'date': data.date.date(),  
                'time': formatted_time,
                'message': data.message 
            }
            data_list.append(data_entry)

        return Response({'message': 'Graph Data.', 'data': data_list}, status=200)
    else:
        return Response({"error": 'Wrong Request Method'}, status=400)

# -------------------------------------------------------------------




 