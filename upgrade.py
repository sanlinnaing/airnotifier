#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2012, Dongsheng Cai
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Dongsheng Cai nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL DONGSHENG CAI BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
import tornado
import os
import pymongo
from bson import ObjectId
from tornado.options import define, options
from constants import (
    DEVICE_TYPE_IOS,
    KEY_APNS_AUTHKEY,
    KEY_APNS_BUNDLEID,
    KEY_APNS_KEYID,
    KEY_APNS_TEAMID,
)

define("mongouri", default="mongodb://localhost:27017/", help="MongoDB host name")
define("masterdb", default="airnotifier", help="MongoDB DB to store information")
define("appprefix", default="", help="DB name prefix")

if __name__ == "__main__":
    curpath = os.path.dirname(os.path.realpath(__file__))

    tornado.options.parse_config_file("%s/config.py" % curpath)
    tornado.options.parse_command_line()
    mongodb = pymongo.MongoClient(options.mongouri)
    masterdb = mongodb[options.masterdb]

    version_object = masterdb["options"].find_one({"name": "version"})
    appprefix = options.appprefix

    version = version_object["value"]

    if version < 20140315:
        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            appid = ObjectId(app["_id"])
            # Repair application setting collection
            if "blockediplist" not in app:
                app["blockediplist"] = ""
            if "description" not in app:
                app["description"] = ""
            if "gcmprojectnumber" not in app:
                app["gcmprojectnumber"] = ""
            if "gcmapikey" not in app:
                app["gcmapikey"] = ""
            masterdb.applications.update_one({"_id": appid}, {"$set": app}, upsert=True)

            # Adding device to token collections
            db = mongodb[appprefix + appname]
            tokens = db["tokens"].find()
            for token in tokens:
                tokenid = ObjectId(token["_id"])
                if "device" not in token:
                    token["device"] = DEVICE_TYPE_IOS
                    result = db["tokens"].update_one(
                        {"_id": tokenid}, {"$set": token}, upsert=True)

        r = masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20140315}}, upsert=True
        )
        version_object = masterdb["options"].find_one({"name": "version"})

    if version < 20140720:
        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            appid = ObjectId(app["_id"])
            # Repair application setting collection
            if "wnsclientid" not in app:
                app["wnsclientid"] = ""
            if "wnsclientsecret" not in app:
                app["wnsclientsecret"] = ""
            if "wnsaccesstoken" not in app:
                app["wnsaccesstoken"] = ""
            if "wnstokentype" not in app:
                app["wnstokentype"] = ""
            if "wnstokenexpiry" not in app:
                app["wnstokenexpiry"] = ""
            masterdb.applications.update_one({"_id": appid}, {"$set": app}, upsert=True)
        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20140720}}, upsert=True
        )

    if version < 20140814:
        # Don't store fullpath in db, only filename
        import os

        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            appid = ObjectId(app["_id"])
            if "certfile" in app:
                app["certfile"] = os.path.basename(app.get("certfile"))
            if "keyfile" in app:
                app["keyfile"] = os.path.basename(app.get("keyfile"))
            if "mpnscertificatefile" in app:
                app["mpnscertificatefile"] = os.path.basename(
                    app.get("mpnscertificatefile")
                )
            masterdb.applications.update_one({"_id": appid}, {"$set": app}, upsert=True)
        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20140814}}, upsert=True
        )

    if version < 20140820:
        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            appid = ObjectId(app["_id"])
            # Repair application setting collection
            if "clickatellusername" not in app:
                app["clickatellusername"] = ""
            if "clickatellpassword" not in app:
                app["clickatellpassword"] = ""
            if "clickatellappid" not in app:
                app["clickatellappid"] = ""
            masterdb.applications.update_one({"_id": appid}, {"$set": app}, upsert=True)
        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20140820}}, upsert=True
        )

    if version < 20151101:
        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            db = mongodb[appprefix + appname]
            indexes = [("created", pymongo.DESCENDING)]
            logging.info(
                ("Adding index to %s%s['tokens'].%s" % (appprefix, appname, "created"))
            )
            db["tokens"].create_index(indexes)
            logging.info(
                ("Adding index to %s%s['logs'].%s" % (appprefix, appname, "created"))
            )
            db["logs"].create_index(indexes)

        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20151101}}, upsert=True
        )

    if version < 20190125:
        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20190125}}, upsert=True
        )

    if version < 20190825:
        users = masterdb.managers.find()
        for user in users:
            #  appname = app["shortname"]
            # Repair application setting collection
            if "orgid" not in user:
                masterdb.managers.find_one_and_update(
                    {"username": user["username"]}, {"$set": {"orgid": 0}}
                )
            if "email" not in user:
                masterdb.managers.find_one_and_update(
                    {"username": user["username"]},
                    {"$set": {"email": user["username"]}},
                )
        apps = masterdb.applications.find()
        for app in apps:
            if "orgid" not in app:
                masterdb.applications.find_one_and_update(
                    {"shortname": app["shortname"]}, {"$set": {"orgid": 0}}
                )
            #  if not "clickatellpassword" in app:
            #  app["clickatellpassword"] = ""
            #  if not "clickatellappid" in app:
            #  app["clickatellappid"] = ""
        #  masterdb["options"].update_one(
        #  {"name": "version"}, {"$set": {"value": 20190814}}, upsert=True
        #  )
        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20190825}}, upsert=True
        )
    if version < 20191117:
        masterdb.managers.create_index([('email', pymongo.ASCENDING)], unique=True)
        try:
            masterdb.managers.drop_index("user")
        except Exception as ex:
            logging.error(ex)

        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20191117}}, upsert=True
        )
    if version < 20191213.01:
        apps = masterdb.applications.find()
        for app in apps:
            appname = app["shortname"]
            appid = ObjectId(app["_id"])
            if KEY_APNS_AUTHKEY not in app:
                app[KEY_APNS_AUTHKEY] = ""
            if KEY_APNS_BUNDLEID not in app:
                app[KEY_APNS_BUNDLEID] = ""
            if KEY_APNS_KEYID not in app:
                app[KEY_APNS_KEYID] = ""
            if KEY_APNS_TEAMID not in app:
                app[KEY_APNS_TEAMID] = ""
            masterdb.applications.update_one({"_id": appid}, {"$set": app}, upsert=True)
            masterdb.applications.update_one(
                {"_id": appid},
                {
                    "$unset": {
                        "gcmprojectnumber": "",
                        "gcmapikey": "",
                        "connections": "",
                        "enableapns": "",
                        "environment": "",
                    }
                },
                upsert=True,
            )

        masterdb["options"].update_one(
            {"name": "version"}, {"$set": {"value": 20191213.01}}, upsert=True
        )

    version_object = masterdb["options"].find_one({"name": "version"})
    version = version_object["value"]
    logging.info("Upgraded, you're using version: %d" % version)
