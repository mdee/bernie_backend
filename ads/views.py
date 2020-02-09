import datetime

from django.db.models import Min
from django.shortcuts import render
from django.http import HttpResponse

from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateFilter
from rest_framework import generics, viewsets, status
from rest_framework.response import Response

from .models import Ad, PresidentialCampaign, IndividualDonation
from .serializers import AdSerializer, PresidentialCampaignSerializer, DateExtentSerializer, DateExtent, \
    DateAdMetaSerializer, AdMeta, DateAdMeta, AdMetaSerializer, DateDonationMetaSerializer, DateDonationMeta
from dateutil.relativedelta import relativedelta

DASH_DATE_FORMAT = '%Y-%m-%d'

class DateDonationMetaList(viewsets.ViewSet):
    """"""
    serializer_class = DateDonationMetaSerializer

    def list(self, request):
        """"""
        # This method gets a campaign name, a start date, and an end date. If those aren't present, it's a bad request
        campaign_name = request.query_params.get('campaign_name', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        all_params_present = campaign_name and start_date and end_date
        if not all_params_present:
            return Response('Missing required parameter for DateDonationMetaList', status=status.HTTP_400_BAD_REQUEST)
        start_date = datetime.datetime.strptime(start_date, DASH_DATE_FORMAT).date()
        end_date = datetime.datetime.strptime(end_date, DASH_DATE_FORMAT).date()
        query_arg_dict = {'presidential_campaign__name': campaign_name, 'date__gte': start_date, 'date__lte': end_date}

        # Now, fetch all donations that match
        donations_in_date_range = IndividualDonation.objects.filter(**query_arg_dict).extra(order_by=['date'])
        # Generate the range of dates that was queried
        date_delta = end_date - start_date
        date_range_list = [start_date + datetime.timedelta(days=i) for i in range(date_delta.days + 1)]
        # Create a dict of strings to date_range_list entries
        date_range_strings = [d.strftime(DASH_DATE_FORMAT) for d in date_range_list]
        date_range_dict = {date_key: 0 for date_key in date_range_strings}
        # Now, iterate over all donations and increment the counts
        for donation in donations_in_date_range:
            date_key = donation.date.strftime(DASH_DATE_FORMAT)
            date_range_dict[date_key] += 1
        # Now, serialize
        date_donations = []
        for date_key, count in date_range_dict.items():
            date = datetime.datetime.strptime(date_key, DASH_DATE_FORMAT).date()
            date_donation_serializer = DateDonationMetaSerializer(DateDonationMeta(date=date, count=count))
            date_donations.append(date_donation_serializer.data)
        return Response(date_donations)


class DateExtentList(viewsets.ViewSet):
    """"""
    serializer_class = DateExtentSerializer
    DEFAULT_MONTH_DELTA = 1

    def list(self, request):
        """"""
        month_delta = request.query_params.get('month_delta', self.DEFAULT_MONTH_DELTA)
        # Get all Ad values for start + end date, and then pop off the first and last to create a DateExtent
        ad_date_values = Ad.objects.values('start_date', 'end_date').extra(order_by=['start_date', 'end_date'])
        min_date = ad_date_values.first()['start_date']
        max_date = ad_date_values.last()['end_date']
        # Dial back `month_delta` amount
        start_date = max_date + relativedelta(months=-int(month_delta))
        # Create a new DateExtent
        date_extent = DateExtent(min_date=min_date, max_date=max_date, start_date=start_date)
        serializer = DateExtentSerializer(date_extent)
        return Response(serializer.data)


class DateRangeAdMetaList(viewsets.ViewSet):
    """
    """
    serializer_class = DateAdMetaSerializer

    def list(self, request):
        """"""
        # This method gets a campaign name, a start date, and an end date. If those aren't present, it's a bad request
        campaign_name = request.query_params.get('campaign_name', None)
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        # Optional args vv
        ad_type = request.query_params.get('ad_type', None)
        all_params_present = campaign_name and start_date and end_date
        if not all_params_present:
            return Response('Missing required parameter for DateRangeAdMetaList', status=status.HTTP_400_BAD_REQUEST)
        # Now, you want to fetch all Ads for this campaign, within those dates
        start_date = datetime.datetime.strptime(start_date, DASH_DATE_FORMAT).date()
        end_date = datetime.datetime.strptime(end_date, DASH_DATE_FORMAT).date()
        query_arg_dict = {'presidential_campaign__name': campaign_name, 'start_date__gte': start_date,
                          'end_date__lt': end_date}
        if ad_type:
            query_arg_dict['ad_type'] = ad_type
        # Execute the query and get all of the ads
        ads_in_date_range = Ad.objects.filter(**query_arg_dict).extra(order_by=['start_date', 'end_date'])
        # Generate the range of dates that was queried
        date_delta = end_date - start_date
        date_range_list = [start_date + datetime.timedelta(days=i) for i in range(date_delta.days + 1)]
        # Create a dict of strings to date_range_list entries
        date_range_strings = [d.strftime(DASH_DATE_FORMAT) for d in date_range_list]
        spend_range_set = set()
        impressions_range_set = set()
        ad_type_set = set()
        date_range_dict = {date_string: {'spend_range': {}, 'impressions_range': {}, 'ad_type': {}}
                           for date_string in date_range_strings}
        for ad in ads_in_date_range:
            # This ad has a spend_range, an impressions_range, and an ad_type
            # We want to generate the range of dates this ad ran
            ad_data_delta = ad.end_date - ad.start_date
            ad_date_range = [ad.start_date + datetime.timedelta(days=i) for i in range(ad_data_delta.days)]
            # Add this data to the sets
            spend_range_set.add(ad.spend_range)
            impressions_range_set.add(ad.impressions_range)
            ad_type_set.add(ad.ad_type)
            for date in ad_date_range:
                # Convert this to a string to use as key
                date_key = date.strftime(DASH_DATE_FORMAT)
                # Pull this date dict out
                date_dict = date_range_dict[date_key]
                # Ensure the attribute keys are there
                if ad.spend_range not in date_dict['spend_range']:
                    date_dict['spend_range'][ad.spend_range] = 0
                if ad.impressions_range not in date_dict['impressions_range']:
                    date_dict['impressions_range'][ad.impressions_range] = 0
                if ad.ad_type not in date_dict['ad_type']:
                    date_dict['ad_type'][ad.ad_type] = 0
                # Increment the count
                date_dict['spend_range'][ad.spend_range] += 1
                date_dict['impressions_range'][ad.impressions_range] += 1
                date_dict['ad_type'][ad.ad_type] += 1
        # Go through each date, and each attribute, and fill out the set
        for date_key, date_dict in date_range_dict.items():
            for spend_range in spend_range_set:
                if spend_range not in date_dict['spend_range']:
                    date_dict['spend_range'][spend_range] = 0
            for impressions_range in impressions_range_set:
                if impressions_range not in date_dict['impressions_range']:
                    date_dict['impressions_range'][impressions_range] = 0
            for ad_type in ad_type_set:
                if ad_type not in date_dict['ad_type']:
                    date_dict['ad_type'][ad_type] = 0
            date_range_dict[date_key] = date_dict
        # Time to serialize
        date_ad_metas = []
        for date_key, date_dict in date_range_dict.items():
            spend_ranges = []
            for spend_range, count in date_dict['spend_range'].items():
                spend_range_meta = AdMeta(label=spend_range, count=count)
                spend_range_serializer = AdMetaSerializer(spend_range_meta)
                spend_ranges.append(spend_range_serializer.data)
            impressions_ranges = []
            for impressions_range, count in date_dict['impressions_range'].items():
                impressions_range_meta = AdMeta(label=impressions_range, count=count)
                impressions_range_serializer = AdMetaSerializer(impressions_range_meta)
                impressions_ranges.append(impressions_range_serializer.data)
            ad_types = []
            for ad_type, count in date_dict['ad_type'].items():
                ad_type_meta = AdMeta(label=ad_type, count=count)
                ad_meta_serializer = AdMetaSerializer(ad_type_meta)
                ad_types.append(ad_meta_serializer.data)
            # Create a date
            date = datetime.datetime.strptime(date_key, DASH_DATE_FORMAT).date()
            date_ad_meta = DateAdMeta(date=date, spend_ranges=spend_ranges, impressions_ranges=impressions_ranges,
                                      ad_types=ad_types)
            date_ad_meta_serializer = DateAdMetaSerializer(date_ad_meta)
            date_ad_metas.append(date_ad_meta_serializer.data)
        return Response(date_ad_metas)


class AdList(viewsets.ModelViewSet):
    serializer_class = AdSerializer

    def get_queryset(self):
        """"""
        # Campaign name is required
        campaign_name = self.request.query_params.get('campaign_name', None)
        # Start date + end date are required
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        # Additional options are spend range, impessions range, and ad type
        spend_range = self.request.query_params.get('spend_range', None)
        ad_type = self.request.query_params.get('ad_type', None)
        impressions_range = self.request.query_params.get('impressions_range', None)

        all_params_present = campaign_name and start_date and end_date
        if not all_params_present:
            return Response('Missing required parameter for DateRangeAdMetaList', status=status.HTTP_400_BAD_REQUEST)

        start_date = datetime.datetime.strptime(start_date, DASH_DATE_FORMAT).date()
        end_date = datetime.datetime.strptime(end_date, DASH_DATE_FORMAT).date()
        query_arg_dict = {'presidential_campaign__name': campaign_name, 'start_date__gte': start_date, 'end_date__lte': end_date + datetime.timedelta(days=1)}
        # Add in optional args
        if spend_range:
            query_arg_dict['spend_range'] = spend_range
        if ad_type:
            query_arg_dict['ad_type'] = ad_type
        if impressions_range:
            query_arg_dict['impressions_range'] = impressions_range
        return Ad.objects.filter(**query_arg_dict)

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    # filterset_class = AdFilter
    ordering_fields = ['start_date', 'end_date']
    ordering = ['start_date', 'end_date', 'spend_range', 'impressions_range', 'ad_type']


class PresidentialCampaignList(viewsets.ReadOnlyModelViewSet):
    serializer_class = PresidentialCampaignSerializer
    queryset = PresidentialCampaign.objects.all()
    filter_backends = [OrderingFilter]
    ordering = ['name']
