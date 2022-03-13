from django.contrib import admin

# Register your models here.
from .models import Post,TheaterWinBookRecord,TheaterWinQuestion,\
                    TheaterWinQuestionInfo,TheaterWinQuestionReply, \
                    Full_Chatting_Message, TheaterWinBookRecordInfo, \
                    TheaterWinBookRecordReply, StockSummaryKr, StockIfrsKr, StockGroupKr, FullvestingApi

admin.site.register(Post)
admin.site.register(TheaterWinBookRecord)
admin.site.register(TheaterWinQuestion)
admin.site.register(TheaterWinQuestionInfo)
admin.site.register(TheaterWinQuestionReply)
admin.site.register(Full_Chatting_Message)
admin.site.register(TheaterWinBookRecordInfo)
admin.site.register(TheaterWinBookRecordReply)
admin.site.register(StockSummaryKr)
admin.site.register(StockIfrsKr)
admin.site.register(StockGroupKr)
admin.site.register(FullvestingApi)