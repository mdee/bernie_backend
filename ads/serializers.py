from rest_framework import serializers
from .models import Ad, PresidentialCampaign


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'link',
            'spend_range',
            'start_date',
            'end_date',
            'impressions_range',
            'ad_type',
        )
        model = Ad


class PresidentialCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name'
        )
        model = PresidentialCampaign


class DateExtent(object):
    """"""

    def __init__(self, min_date, max_date, start_date):
        """"""
        self.min_date = min_date
        self.max_date = max_date
        self.start_date = start_date


class DateExtentSerializer(serializers.Serializer):
    """
    Will return the extent of dates (So 2 elements) for all Ads in database
    """

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    min_date = serializers.DateField()
    max_date = serializers.DateField()
    start_date = serializers.DateField()


class AdMeta(object):
    """"""

    def __init__(self, label, count):
        """"""
        self.label = label
        self.count = count


class AdMetaSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    label = serializers.CharField(max_length=25)
    count = serializers.IntegerField(default=0)


class DateAdMeta(object):
    """"""

    def __init__(self, date, spend_ranges, impressions_ranges, ad_types):
        """"""
        self.date = date
        self.spend_ranges = spend_ranges
        self.impressions_ranges = impressions_ranges
        self.ad_types = ad_types


class DateAdMetaSerializer(serializers.Serializer):
    """
    """

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    date = serializers.DateField()
    spend_ranges = serializers.ListField()
    impressions_ranges = serializers.ListField()
    ad_types = serializers.ListField()


class DateDonationMeta(object):
    """"""

    def __init__(self, date, count):
        """"""
        self.date = date
        self.count = count


class DateDonationMetaSerializer(serializers.Serializer):
    """"""

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    date = serializers.DateField()
    count = serializers.IntegerField()
