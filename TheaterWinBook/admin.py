from django.contrib import admin

# Register your models here.
from .models import Post,TheaterWinBookRecord,TheaterWinQuestion,\
                    TheaterWinQuestionInfo,TheaterWinQuestionReply, \
                    Full_Chatting_Message, TheaterWinBookRecordInfo, \
                    TheaterWinBookRecordReply, StockSummaryKr, StockIfrsKr, StockGroupKr, FullvestingApi, \
                    StockList

from .models_freeboard import FreeBoard, FreeBoardInfo, FreeBoardReply
from .models_freeboardstock import FreeBoardstock, FreeBoardstockInfo, FreeBoardstockReply
from .models_freeboardprof import FreeBoardprof, FreeBoardprofInfo, FreeBoardprofReply

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
admin.site.register(StockList)

admin.site.register(FreeBoard)
admin.site.register(FreeBoardInfo)
admin.site.register(FreeBoardReply)


admin.site.register(FreeBoardstock)
admin.site.register(FreeBoardstockInfo)
admin.site.register(FreeBoardstockReply)

admin.site.register(FreeBoardprof)
admin.site.register(FreeBoardprofInfo)
admin.site.register(FreeBoardprofReply)