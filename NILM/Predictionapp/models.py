from django.db.models import Model, Index, CASCADE

from django.db.models import AutoField, TextField, FloatField, ForeignKey, DateTimeField, BooleanField, OneToOneField

from django.contrib.auth.models import User

class House(Model):
    user = OneToOneField(User, primary_key=True)
    Mean = FloatField(default=0)
    Std = FloatField(default=0)

    @property
    def username(self):
        return self.user.get_username()

    @property
    def appliances(self):
        building_appliances = Appliance.objects.filter(house = self)
        return (appliance.appliance_Name for appliance in building_appliances)

class Appliance(Model):
    appliance_ID = AutoField(primary_key=True, unique=True)
    appliance_Name = TextField(default='Unknown')
    house = ForeignKey(House, on_delete=CASCADE)
    mean = FloatField(default=0)
    std = FloatField(default=1)

    class Meta:
        indexes = [
            Index(fields=['house']),
            Index(fields=['house', 'appliance_Name'])
        ]

        unique_together = ('appliance_ID', 'house')

    @property
    def username(self):
        return self.house.username

class Aggregate(Model):
    Record_ID = AutoField(primary_key=True, unique=True)
    Date_Time = DateTimeField(auto_now_add = True)
    house = ForeignKey(House, on_delete=CASCADE)
    Power_Consumption = FloatField(default=0)

    class Meta:
        indexes = [
            Index(fields=['house']),
            Index(fields=['house', 'Date_Time'])
        ]

        unique_together = ('house, Date_Time')

        ordering = ['-Date_Time']

class Predictions(Model):
    Prediction_ID = AutoField(primary_key=True, unique= True)
    aggregate = ForeignKey(Aggregate, on_delete=CASCADE)
    appliance = ForeignKey(Appliance, on_delete=CASCADE)
    prediction = FloatField(default=0)
    completed = BooleanField(default = 0)

    class Meta:
        indexes = [
            Index(fields = ['aggregate']),
            Index(fields = ['appliance']),
            Index(fields = ['aggregate', 'appliance'])
        ]

        unique_together = ('aggregate','appliance')

        ordering = ['appliance']
