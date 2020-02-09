from django.db import models


class PresidentialCampaign(models.Model):
    name = models.CharField(max_length=100)
    google_campaign_id = models.CharField(max_length=100)
    fec_id = models.CharField(max_length=9)


class Ad(models.Model):
    presidential_campaign = models.ForeignKey(PresidentialCampaign, on_delete=models.CASCADE)
    google_ad_id = models.CharField(max_length=100)
    start_date = models.DateField('start date')
    end_date = models.DateField('end date')
    number_of_days = models.IntegerField(default=0)
    link = models.URLField(max_length=500)
    ad_type = models.CharField(max_length=25)
    spend_range = models.CharField(max_length=50)
    impressions_range = models.CharField(max_length=50)


class IndividualDonation(models.Model):
    date = models.DateField('date')
    presidential_campaign = models.ForeignKey(PresidentialCampaign, on_delete=models.CASCADE)
