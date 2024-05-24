from .models import GraphData, Logs

def oneData(**kwargs):
    try:
        graph_data = GraphData.objects.create(**kwargs)
        return True
    except Exception as e:
        print(f"Error saving graph data: {e}")

def updateData(id, **kwargs):
    try:
        kwargs.pop('currentGraphId', None)
        graph_data = GraphData.objects.filter(id=id).update(**kwargs)
        return True
    except Exception as e:
        print(f"Error saving graph data: {e}")

def Graph(accessType, msg,**kwargs):
    try:
        kwargs.pop('currentGraphId', None)
        graph_data = GraphData.objects.create(**kwargs)

        logs_data = Logs.objects.create(accessType=accessType, message=f'{msg} Graph', graph_id=graph_data.id, **kwargs)
        return True
    except Exception as e:
        print(f"Error saving graph data: {e}")
        return False
    

def logsData(collaborator, msg,**kwargs):
    try:
        Logs.objects.create(collaborator=collaborator, message=f'{msg} Graph', **kwargs)
        return True
    except Exception as e:
        print(f"Error saving graph data: {e}")
        return False


