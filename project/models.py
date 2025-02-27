from django.db import models
from account.models import User

class Working(models.Model):
    filename = models.CharField(max_length=255)
    date = models.DateTimeField()

    
class Project(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    modified_date = models.DateTimeField(null=True, blank=True)


class File(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    modified_date = models.DateTimeField(null=True, blank=True)


class Trash(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, null=True, blank=True)
    projectcreatedate = models.DateTimeField()
    filecreatedate = models.CharField(max_length=255, null=True, blank=True)
    modifydate = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField()


class Notification(models.Model):
    sender = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='owned_shared_projects', null=True)
    receiver = models.ForeignKey('account.User', on_delete=models.CASCADE, null=True)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    message = models.CharField(max_length=255, null=True)
    role = models.CharField(max_length=255, null=True)
    read = models.CharField(max_length=255)
    toast = models.CharField(max_length=255)
    acceptance = models.CharField(max_length=255, null=True)
    pre_accept = models.CharField(max_length=255, null=True)
    date = models.DateTimeField()

    
class Associate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='associated_projects')
    role = models.CharField(max_length=255)
    date = models.DateTimeField()
    modifydate = models.CharField(max_length=255, null=True, blank=True)


class Archived(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='archived_projects')
    role = models.CharField(max_length=255)
    date = models.DateTimeField()
    modifydate = models.CharField(max_length=255, null=True, blank=True)


class GraphData(models.Model):
    graphName = models.CharField(max_length=100, null=True, blank=True)
    xAxis = models.CharField(max_length=100, null=True, blank=True)
    yAxis = models.CharField(max_length=100, null=True, blank=True)
    parameters = models.JSONField(null=True, blank=True)
    barColors = models.JSONField(null=True, blank=True)
    selectedLabels = models.JSONField(null=True, blank=True)
    xLabelColor = models.CharField(max_length=100, null=True, blank=True)
    yLabelColor = models.CharField(max_length=100, null=True, blank=True)
    graphHeadSize = models.IntegerField(null=True, blank=True)
    graphHeadWeight = models.CharField(max_length=100, null=True, blank=True)
    xLabelSize = models.IntegerField(null=True, blank=True)
    xLabelWeight = models.CharField(max_length=100, null=True, blank=True)
    yLabelSize = models.IntegerField(null=True, blank=True)
    yLabelWeight = models.CharField(max_length=100, null=True, blank=True)
    graphHeading = models.CharField(max_length=100, null=True, blank=True)
    barBorders = models.IntegerField(null=True, blank=True)
    condition = models.JSONField(null=True, blank=True)
    conditionalParameters = models.JSONField(null=True, blank=True)
    yAxisConditions = models.JSONField(null=True, blank=True)
    yAxisValue = models.CharField(max_length=100, null=True, blank=True)
    textureColor = models.CharField(max_length=100, null=True, blank=True)
    textureBg = models.CharField(max_length=100, null=True, blank=True)
    legends = models.CharField(max_length=100, null=True, blank=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    colorStatesTexture = models.JSONField(null=True, blank=True)
    colorStatesBgTexture = models.JSONField(null=True, blank=True)
    dictionaryState = models.JSONField(null=True, blank=True)
    borderColor = models.CharField(max_length=100, null=True, blank=True)
    dlSize = models.IntegerField(null=True, blank=True)
    dlWeight = models.CharField(max_length=100, null=True, blank=True)
    dlColor = models.CharField(max_length=100, null=True, blank=True)
    stepped = models.BooleanField(null=True, blank=True)
    dataLabelsConfig = models.BooleanField(null=True, blank=True)
    fontFamily = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    file_id = models.IntegerField(null=True, blank=True)
    stepSize = models.CharField(max_length=100, null=True, blank=True)
    legendPosition = models.CharField(max_length=100, null=True, blank=True)
    greyShadeCheck = models.CharField(max_length=100, null=True, blank=True)
    smoothness = models.BooleanField(null=True, blank=True)


class Logs(models.Model):
    user_id = models.BigIntegerField()
    accessType = models.CharField(max_length=255, null=True, blank=True)
    project_id = models.BigIntegerField(null=True, blank=True)
    file_id = models.BigIntegerField(null=True, blank=True)
    graph_id = models.BigIntegerField(null=True)
    graphName = models.CharField(max_length=100, null=True, blank=True)
    xAxis = models.CharField(max_length=100, null=True, blank=True)
    yAxis = models.CharField(max_length=100, null=True, blank=True)
    parameters = models.JSONField(max_length=1000, null=True, blank=True)
    barColors = models.JSONField(null=True, blank=True)
    selectedLabels = models.JSONField(null=True, blank=True)
    xLabelColor = models.CharField(max_length=100, null=True, blank=True)
    yLabelColor = models.CharField(max_length=100, null=True, blank=True)
    graphHeadSize = models.IntegerField(null=True, blank=True)
    graphHeadWeight = models.CharField(max_length=100, null=True, blank=True)
    xLabelSize = models.IntegerField(null=True, blank=True)
    xLabelWeight = models.CharField(max_length=100, null=True, blank=True)
    yLabelSize = models.IntegerField(null=True, blank=True)
    yLabelWeight = models.CharField(max_length=100, null=True, blank=True)
    graphHeading = models.CharField(max_length=100, null=True, blank=True)
    barBorders = models.IntegerField(null=True, blank=True)
    condition = models.JSONField(null=True, blank=True)
    conditionalParameters = models.JSONField(null=True, blank=True)
    yAxisConditions = models.JSONField(null=True, blank=True)
    yAxisValue = models.CharField(max_length=100, null=True, blank=True)
    textureColor = models.CharField(max_length=100, null=True, blank=True)
    textureBg = models.CharField(max_length=100, null=True, blank=True)
    legends = models.CharField(max_length=100, null=True, blank=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    colorStatesTexture = models.JSONField(null=True, blank=True)
    colorStatesBgTexture = models.JSONField(null=True, blank=True)
    dictionaryState = models.JSONField(null=True, blank=True)
    borderColor = models.CharField(max_length=100, null=True, blank=True)
    dlSize = models.IntegerField(null=True, blank=True)
    dlWeight = models.CharField(max_length=100, null=True, blank=True)
    dlColor = models.CharField(max_length=100, null=True, blank=True)
    stepped = models.BooleanField(null=True, blank=True)
    dataLabelsConfig = models.BooleanField(null=True, blank=True)
    fontFamily = models.CharField(max_length=100, null=True, blank=True)
    stepSize = models.CharField(max_length=100, null=True, blank=True)
    legendPosition = models.CharField(max_length=100, null=True, blank=True)
    greyShadeCheck = models.CharField(max_length=100, null=True, blank=True)
    message = models.CharField(max_length=255, null=True, blank=True)
    smoothness = models.BooleanField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

 