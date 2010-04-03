# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_list_or_404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.cache import cache
from apps.rss_feeds.models import Feed
from apps.reader.models import UserSubscription, UserSubscriptionFolders
from utils import json
import utils.opml as opml
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest
from django.core import serializers 
from pprint import pprint
from django.db import IntegrityError
import datetime
import codecs


def opml_upload(request):
    xml_opml = None
    message = "OK"
    code = 1
    
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            xml_opml = file.read()
            
    opml_importer = OPMLImporter(xml_opml, request.user)
    folders = opml_importer.process()

    feeds = UserSubscription.objects.filter(user=request.user).values()
    data = json.encode(dict(message=message, code=code, payload=dict(folders=folders, feeds=feeds)))

    return HttpResponse(data, mimetype='text/plain')

class OPMLImporter:
    
    def __init__(self, opml_xml, user):
        self.user = user
        self.opml_xml = opml_xml

    def process(self):
        outline = opml.from_string(self.opml_xml)
        self.clear_feeds()
        folders = self.process_outline(outline)
        UserSubscriptionFolders.objects.create(user=self.user, folders=json.encode(folders))

        return folders
    
    def clear_feeds(self):
        UserSubscriptionFolders.objects.filter(user=self.user).delete()
        UserSubscription.objects.filter(user=self.user).delete()
        
    def process_outline(self, outline):
        folders = []
    
        for item in outline:
            if not hasattr(item, 'xmlUrl'):
                folder = item
                print 'New Folder: %s' % folder.text
                folders.append({folder.text: self.process_outline(folder)})
            elif hasattr(item, 'xmlUrl'):
                feed = item
                if not hasattr(feed, 'htmlUrl'):
                    setattr(feed, 'htmlUrl', None)
                if not hasattr(feed, 'title'):
                    setattr(feed, 'title', feed.htmlUrl)
                print '\t%s - %s - %s' % (feed.title, feed.htmlUrl, feed.xmlUrl,)
                feed_data = dict(feed_address=feed.xmlUrl, feed_link=feed.htmlUrl, feed_title=feed.title)
                # feeds.append(feed_data)
                feed_db, _ = Feed.objects.get_or_create(feed_address=feed.xmlUrl, defaults=dict(**feed_data))
                us, _ = UserSubscription.objects.get_or_create(feed=feed_db, user=self.user)
                folders.append(feed_db.pk)
        return folders
    
if __name__ == '__main__':
    opml_string = """<?xml version="1.0" encoding="UTF-8"?>
<!-- OPML generated by NetNewsWire -->
<opml version="1.1">
	<head>
		<title>mySubscriptions</title>
		</head>
	<body>
		<outline text="New York" title="New York">
			<outline text="Brownstoner" description="" title="Brownstoner" type="rss" version="RSS" htmlUrl="http://www.brownstoner.com/" xmlUrl="http://www.brownstoner.com/index.xml"/>
			<outline text="Gothamist" description="" title="Gothamist" type="rss" version="RSS" htmlUrl="http://gothamist.com/" xmlUrl="http://gothamist.com/index.rdf"/>
			<outline text="Brokelyn" description="" title="Brokelyn" type="rss" version="RSS" htmlUrl="http://www.brokelyn.com" xmlUrl="http://www.brokelyn.com/feed/"/>
			<outline text="Streetsblog New York City" description="" title="Streetsblog New York City" type="rss" version="RSS" htmlUrl="http://www.streetsblog.org" xmlUrl="http://www.streetsblog.org/feed/"/>
			<outline text="The Corduroy Appreciation Club" description="" title="The Corduroy Appreciation Club" type="rss" version="RSS" htmlUrl="http://corduroyclub.com" xmlUrl="http://corduroyclub.com/feed"/>
			<outline text="FREEwilliamsburg" description="" title="FREEwilliamsburg" type="rss" version="RSS" htmlUrl="http://www.freewilliamsburg.com/" xmlUrl="http://www.freewilliamsburg.com/atom.xml"/>
			<outline text="Scouting NY" description="" title="Scouting NY" type="rss" version="RSS" htmlUrl="http://www.scoutingny.com" xmlUrl="http://www.scoutingny.com/?feed=rss2"/>
			<outline text="very small array" description="" title="very small array" type="rss" version="RSS" htmlUrl="http://www.verysmallarray.com" xmlUrl="http://www.verysmallarray.com/?feed=rss2"/>
			<outline text="Frugal Traveler" description="" title="Frugal Traveler" type="rss" version="RSS" htmlUrl="http://frugaltraveler.blogs.nytimes.com/" xmlUrl="http://frugaltraveler.blogs.nytimes.com/feed/"/>
			</outline>
		<outline text="Tech" title="Tech">
			<outline text="Joel on Software" description="" title="Joel on Software" type="rss" version="RSS" htmlUrl="http://www.joelonsoftware.com" xmlUrl="http://www.joelonsoftware.com/rss.xml"/>
			<outline text="Daring Fireball" description="" title="Daring Fireball" type="rss" version="RSS" htmlUrl="http://daringfireball.net/" xmlUrl="http://daringfireball.net/index.xml"/>
			<outline text="Techcrunch" description="" title="Techcrunch" type="rss" version="RSS" htmlUrl="http://techcrunch.com" xmlUrl="http://feeds.feedburner.com/Techcrunch"/>
			<outline text="Coding Horror" description="" title="Coding Horror" type="rss" version="RSS" htmlUrl="http://www.codinghorror.com/blog/" xmlUrl="http://feeds.feedburner.com/codinghorror/"/>
			<outline text="John Resig" description="" title="John Resig" type="rss" version="RSS" htmlUrl="http://ejohn.org" xmlUrl="http://feeds.feedburner.com/JohnResig"/>
			<outline text="Ted Dziuba" description="" title="Ted Dziuba" type="rss" version="RSS" htmlUrl="http://teddziuba.com/" xmlUrl="http://teddziuba.com/atom.xml"/>
			<outline text="Ajaxian » Front Page" description="" title="Ajaxian » Front Page" type="rss" version="RSS" htmlUrl="http://ajaxian.com" xmlUrl="http://ajaxian.com/index.xml"/>
			<outline text="James Padolsey" description="" title="James Padolsey" type="rss" version="RSS" htmlUrl="http://james.padolsey.com" xmlUrl="http://james.padolsey.com/feed/"/>
			<outline text="David Cramer's Blog" description="" title="David Cramer's Blog" type="rss" version="RSS" htmlUrl="http://www.davidcramer.net" xmlUrl="http://www.davidcramer.net/feed"/>
			<outline text="MacRumors : Mac News and Rumors" description="" title="MacRumors : Mac News and Rumors" type="rss" version="RSS" htmlUrl="http://www.macrumors.com" xmlUrl="http://www.macrumors.com/macrumors.xml"/>
			<outline text="wonko.com" description="" title="wonko.com" type="rss" version="RSS" htmlUrl="http://wonko.com/" xmlUrl="http://feeds.feedburner.com/wonko"/>
			<outline text="Devthought" description="" title="Devthought" type="rss" version="RSS" htmlUrl="http://devthought.com" xmlUrl="http://feeds2.feedburner.com/devthought?format=xml"/>
			<outline text="jQuery Blog" description="" title="jQuery Blog" type="rss" version="RSS" htmlUrl="http://blog.jquery.com" xmlUrl="http://blog.jquery.com/feed/"/>
			<outline text="Hacker News - Excerpts" description="" title="Hacker News - Excerpts" type="rss" version="RSS" htmlUrl="http://news.ycombinator.com/" xmlUrl="http://andrewtrusty.appspot.com/readability/feed?url=http%3A//news.ycombinator.com/rss"/>
			<outline text="Waxy.org" description="" title="Waxy.org" type="rss" version="RSS" htmlUrl="http://waxy.org/" xmlUrl="http://waxy.org/index.xml"/>
			<outline text="Lazy Pythonista" description="" title="Lazy Pythonista" type="rss" version="RSS" htmlUrl="http://lazypython.blogspot.com/" xmlUrl="http://lazypython.blogspot.com/feeds/posts/default?alt=rss"/>
			<outline text="cdixon.org - chris dixon's blog" description="" title="cdixon.org - chris dixon's blog" type="rss" version="RSS" htmlUrl="http://cdixon.org" xmlUrl="http://cdixon.org/feed/"/>
			<outline text="Bill the Lizard" description="" title="Bill the Lizard" type="rss" version="RSS" htmlUrl="http://www.billthelizard.com/" xmlUrl="http://www.billthelizard.com/feeds/posts/default"/>
			<outline text="inessential.com" description="" title="inessential.com" type="rss" version="RSS" htmlUrl="http://inessential.com/" xmlUrl="http://inessential.com/xml/rss.xml"/>
			</outline>
		<outline text="Blogs" title="Blogs">
			<outline text="You Look Nice Today" description="" title="You Look Nice Today" type="rss" version="RSS" htmlUrl="http://youlooknicetoday.com" xmlUrl="http://youlooknicetoday.com/rss.xml"/>
			<outline text="The Lens and the Eyebrow" description="" title="The Lens and the Eyebrow" type="rss" version="RSS" htmlUrl="http://blog.seemichaelsphotos.com" xmlUrl="http://blog.seemichaelsphotos.com/rss2.aspx"/>
			<outline text="43 Folders" description="" title="43 Folders" type="rss" version="RSS" htmlUrl="http://www.43folders.com" xmlUrl="http://www.43folders.com/rss.xml"/>
			<outline text="The Doree Chronicles" description="" title="The Doree Chronicles" type="rss" version="RSS" htmlUrl="http://doree.tumblr.com/" xmlUrl="http://doree.tumblr.com/rss"/>
			<outline text="the impossible cool." description="" title="the impossible cool." type="rss" version="RSS" htmlUrl="http://theimpossiblecool.tumblr.com/" xmlUrl="http://theimpossiblecool.tumblr.com/rss"/>
			<outline text="kottke.org" description="" title="kottke.org" type="rss" version="RSS" htmlUrl="http://kottke.org/" xmlUrl="http://feeds.kottke.org/main"/>
			<outline text="Philip Greenspun's Weblog" description="" title="Philip Greenspun's Weblog" type="rss" version="RSS" htmlUrl="http://blogs.law.harvard.edu/philg" xmlUrl="http://blogs.law.harvard.edu/philg/feed/"/>
			<outline text="Rands In Repose" description="" title="Rands In Repose" type="rss" version="RSS" htmlUrl="http://www.randsinrepose.com/" xmlUrl="http://www.randsinrepose.com/index.xml"/>
			<outline text="the selby - photos in your space" description="" title="the selby - photos in your space" type="rss" version="RSS" htmlUrl="http://www.theselby.com" xmlUrl="http://feeds2.feedburner.com/Theselby-PhotosInYourSpace?format=xml"/>
			<outline text="The Storybird blog" description="" title="The Storybird blog" type="rss" version="RSS" htmlUrl="http://blog.storybird.com" xmlUrl="http://feeds.feedburner.com/TheStorybirdBlog?format=xml"/>
			<outline text="You are what you share" description="" title="You are what you share" type="rss" version="RSS" htmlUrl="http://markury.com/" xmlUrl="http://markury.com/rss"/>
			<outline text="Bird feed" description="" title="Bird feed" type="rss" version="RSS" htmlUrl="http://storybird.tumblr.com/" xmlUrl="http://storybird.tumblr.com/rss"/>
			<outline text="one day at a time" description="" title="one day at a time" type="rss" version="RSS" htmlUrl="http://abangupjob.tumblr.com/" xmlUrl="http://abangupjob.tumblr.com/rss"/>
			<outline text="Pretty in the City • Karyn Bosnak" description="" title="Pretty in the City • Karyn Bosnak" type="rss" version="RSS" htmlUrl="http://www.prettyinthecity.com/blog/" xmlUrl="http://www.prettyinthecity.com/blog/rss.xml"/>
			<outline text="An Entirely Other Day: Full Feed" description="" title="An Entirely Other Day: Full Feed" type="rss" version="RSS" htmlUrl="http://www.eod.com/blog/" xmlUrl="http://feeds.feedburner.com/eod_full"/>
			<outline text="hipster puppies" description="" title="hipster puppies" type="rss" version="RSS" htmlUrl="http://hipsterpuppies.tumblr.com/" xmlUrl="http://hipsterpuppies.tumblr.com/rss"/>
			<outline text="The Bloglets" title="The Bloglets">
				<outline text="FAIL Blog: Pictures and Videos of Owned, Pwnd and Fail Moments" description="" title="FAIL Blog: Pictures and Videos of Owned, Pwnd and Fail Moments" type="rss" version="RSS" htmlUrl="http://failblog.org" xmlUrl="http://feeds.feedburner.com/failblog"/>
				<outline text="Iconic Photos" description="" title="Iconic Photos" type="rss" version="RSS" htmlUrl="http://iconicphotos.wordpress.com" xmlUrl="http://iconicphotos.wordpress.com/feed/"/>
				<outline text="nerdboyfriend" description="" title="nerdboyfriend" type="rss" version="RSS" htmlUrl="http://nerdboyfriend.com" xmlUrl="http://nerdboyfriend.com/?feed=rss2"/>
				<outline text="The Cellar - Image of the Day" description="" title="The Cellar - Image of the Day" type="rss" version="RSS" htmlUrl="http://cellar.org" xmlUrl="http://cellar.org/external.php?type=rss2&amp;forumids=10"/>
				<outline text="The Sartorialist" description="" title="The Sartorialist" type="rss" version="RSS" htmlUrl="http://thesartorialist.blogspot.com/" xmlUrl="http://thesartorialist.blogspot.com/feeds/posts/default?alt=rss"/>
				</outline>
			</outline>
		<outline text="Cooking" title="Cooking">
			<outline text="Easy Recipes For Everyday Cooking by Savory Sweet Life" description="" title="Easy Recipes For Everyday Cooking by Savory Sweet Life" type="rss" version="RSS" htmlUrl="http://savorysweetlife.com" xmlUrl="http://savorysweetlife.com/?feed=rss2"/>
			<outline text="SALAD &amp; CANDY" description="" title="SALAD &amp; CANDY" type="rss" version="RSS" htmlUrl="http://saladandcandy.com/" xmlUrl="http://saladandcandy.com/rss"/>
			<outline text="smitten kitchen" description="" title="smitten kitchen" type="rss" version="RSS" htmlUrl="http://smittenkitchen.com" xmlUrl="http://feeds.feedburner.com/smittenkitchen"/>
			<outline text="Salt &amp; Fat" description="" title="Salt &amp; Fat" type="rss" version="RSS" htmlUrl="http://saltandfat.com/" xmlUrl="http://saltandfat.com/rss"/>
			</outline>
		<outline text="Samuel Clay's OfBrooklyn.com" description="" title="Samuel Clay's OfBrooklyn.com" type="rss" version="RSS" htmlUrl="http://conesus.com" xmlUrl="http://www.ofbrooklyn.com/feeds/all/"/>
	</body>
</opml>"""
    user = User.objects.get(username='conesus')
    opml_importer = OPMLImporter(opml_string, user)
    data = opml_importer.process()
    print data