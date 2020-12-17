from datetime import datetime

import babel.dates as dates
import requests

LOCALE = "bn_BD"
SHORT_LOCALE = "bn"
WOEID = 1915035


class Responder:
    def _get_local_time(self, _args=None):
        dt = dates.format_time(datetime.now(), format="short", locale="bn_BD")
        return "এখন সময় %s" % dt

    def _not_found(self, _args=None):
        return "দুঃখিত, আমি কমান্ডটি বুঝি নি"

    def _get_local_temp(self, _args=None):
        try:
            r = requests.get("https://www.metaweather.com/api/location/%d/" % WOEID)
            data = r.json()
            weather = data["consolidated_weather"][0]
            min_temp = weather["min_temp"]
            max_temp = weather["max_temp"]
            the_temp = weather["the_temp"]
            return "এখন তাপমাত্রা %g °C, আজ সর্বনিম্ন তাপমাত্রা %g °C ও সর্বোচ্চ তাপমাত্রা %g °C থাকবে" % (
                the_temp,
                min_temp,
                max_temp,
            )
        except Exception as exc:
            print(exc)
            return "এই মুহূর্তে আবহাওয়া তথ্য বের করা সম্ভব হয় নি"

    def get_response(self, intent, args=None):
        meth = getattr(self, "_%s" % intent, lambda _: self._not_found())
        return meth(args)
