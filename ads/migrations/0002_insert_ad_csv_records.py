import os
import re

from django.db import migrations, models
import csv
from datetime import datetime


def load_initial_data(apps, scheme_editor):
    """

    :param apps:
    :param scheme_editor:
    :return:
    """
    Ad = apps.get_model("ads", "Ad")
    PresidentialCampaign = apps.get_model("ads", "PresidentialCampaign")
    IndividualDonation = apps.get_model("ads", "IndividualDonation")
    presidential_campaign_to_fec_id_dict = {
        'MIKE BLOOMBERG 2020 INC': 'C00728154',
        'TOM STEYER 2020': 'C00711614',
        'PETE FOR AMERICA, INC.' : 'C00697441',
        'BERNIE 2020': 'C00696948',
        'WARREN FOR PRESIDENT, INC.': 'C00693234',
        'AMY FOR AMERICA': 'C00696419',
        'BIDEN FOR PRESIDENT': 'C00703975'
    }

    google_ad_id_idx = 0
    url_idx = 1
    ad_type_idx = 2
    google_campaign_id_idx = 4
    advertiser_name_idx = 5
    start_date_idx = 7
    end_date_idx = 8
    num_days_idx = 9
    impressions_idx = 10
    spend_range_idx = 11
    # datetime_fmt = '%Y-%m-%d %H:%M:%S %z'
    datetime_fmt = '%Y-%m-%d'

    # Have a dict which maps campaign name to the Ad index
    campaign_ad_index_map = {}
    campaigns = []
    ads = []

    with open('ads/migrations/google-political-ads-creative-stats.csv') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Iterate past the header
        # cols: 'ad_id', 'ad_url', 'ad_type', 'regions', 'advertiser_id', 'advertiser_name', 'ad_campaigns_list',
        # 'date_range_start', 'date_range_end', 'num_days', 'impressions', 'spend_usd', 'first_served', 'last_served',
        #   'spend_range_min_usd',' 'spend_range_max_usd'
        #
        # We want: 'ad_id', 'ad_url', 'ad_type', 'advertiser_id', 'advertiser_name', 'date_range_start',
        #   'date_range_end', 'num_days', 'impressions', 'spend_usd':
        #    0, 1, 2, 4, 5, 7, 8, 9, 10, 11
        for row in reader:
            campaign_name = row[advertiser_name_idx]
            if campaign_name not in presidential_campaign_to_fec_id_dict:
                print('\t{0} is not a presidential campaign, skipping'.format(campaign_name))
                continue
            google_ad_id = row[google_ad_id_idx]
            link = row[url_idx]
            ad_type = row[ad_type_idx]
            google_campaign_id = row[google_campaign_id_idx]
            start_date = datetime.strptime(row[start_date_idx], datetime_fmt)
            end_date = datetime.strptime(row[end_date_idx], datetime_fmt)
            impressions_range = row[impressions_idx]
            spend_range = row[spend_range_idx]
            number_of_days = int(row[num_days_idx])
            if campaign_name not in campaign_ad_index_map:
                # Create an entry for the campaign, and add a new PresidentialCampaign to a list to be bulk created
                fec_id = presidential_campaign_to_fec_id_dict[campaign_name]
                campaign_ad_index_map[campaign_name] = []
                campaign = PresidentialCampaign(google_campaign_id=google_campaign_id, name=campaign_name,
                                                fec_id=fec_id)
                campaigns.append(campaign)
            # Create an Ad record
            ad = Ad(google_ad_id=google_ad_id, start_date=start_date, end_date=end_date, number_of_days=number_of_days,
                    link=link, ad_type=ad_type, spend_range=spend_range, impressions_range=impressions_range)
            # Append the index of this Ad to the campaign's list of Ads
            campaign_ad_index_map[campaign_name].append(len(ads))
            # Append it to the list of all Ads to be bulk created later
            ads.append(ad)
    # Bulk create all of the PresidentialCampaigns
    PresidentialCampaign.objects.bulk_create(campaigns)
    # Now, iterate over each campaign, and then pull out the Ad indices, put the campaign ID in
    for campaign in campaigns:
        ad_indices = campaign_ad_index_map[campaign.name]
        for ad_index in ad_indices:
            ads[ad_index].presidential_campaign = campaign
    # Now, open the FEC data file and parse out individual presidential campaign donations
    fec_record_regex = re.compile(r'.*\|[A-Za-z]+\|(?P<date>\d{4}2019)\|.*')
    donations = []
    print('Creating donation records...')
    file_names = ['itcont_2020_20010425_20190425.txt', 'itcont_2020_20190426_20190628.txt',
                  'itcont_2020_20190629_20190905.txt', 'itcont_2020_20190906_20191116.txt',
                  'itcont_2020_20191117_20200122.txt']
    for f in file_names:
        with open(os.path.join('~/Downloads/indiv20/by_date', f)) as txt_file:
            for line in txt_file:
                for campaign in campaigns:
                    if campaign.fec_id in line and 'REFUND' not in line:
                        date_search_results = re.search(fec_record_regex, line)
                        if date_search_results is not None:
                            # Create a new IndividualDonation
                            date = datetime.strptime(date_search_results.group('date'), '%m%d%Y').date()
                            print('\t{0}'.format(date))
                            donation = IndividualDonation(date=date, presidential_campaign=campaign)
                            donations.append(donation)
    # Bulk create the Ads
    Ad.objects.bulk_create(ads)
    # Bulk create the IndividualDonations
    IndividualDonation.objects.bulk_create(donations)
    print('Done')


def reverse_func(apps, schema_editor):
    """

    :param apps:
    :param schema_editor:
    :return:
    """
    Ad = apps.get_model("ads", "Ad")
    Ad.objects.all().delete()
    Campaign = apps.get_model("ads", "Campaign")
    Campaign.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ads', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, reverse_func)
    ]
