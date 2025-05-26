import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
# from django.utils.datetime_safe import datetime
from tinymce import models as tinymce_models
# import FinanceDataReader as fdr
from django.utils.timezone import now
from datetime import datetime


class StockGroupKr(models.Model):
    bat_time = models.DateTimeField(default=datetime.now , blank = False)
    info_date = models.DateField(default=datetime.now , blank=False)
    stock_code = models.CharField(max_length=10, blank=False)
    stock_country = models.CharField(max_length=1, blank=False)
    vesting_type = models.CharField(max_length=1, blank=False)
    # vesting_type_detail = models.CharField(max_length=1, blank=False)
    stock_name = models.CharField(max_length=15, blank=True)
    stock_group = models.CharField(max_length=30, blank=True)
    stock_theme = models.CharField(max_length=30, blank=True)
    etc1_string = models.CharField(max_length=1, blank=True)
    etc2_string = models.CharField(max_length=1, blank=True)
    etc3_string = models.CharField(max_length=1, blank=True)
    etc4_string = models.CharField(max_length=1, blank=True)
    etc5_string = models.CharField(max_length=1, blank=True)
    etc1_int = models.SmallIntegerField(blank=True, null=True)
    etc2_int = models.SmallIntegerField(blank=True, null=True)
    etc3_int = models.SmallIntegerField(blank=True, null=True)
    etc4_int = models.SmallIntegerField(blank=True, null=True)
    etc5_int = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("info_date","stock_code","stock_country","vesting_type")


class StockList(models.Model):
    # stocklist는 중복으로 들어오면 삭제하니 지우자
    # bat_time = models.DateTimeField(default=datetime.now, blank = True)
    stock_code_full = models.CharField(max_length=14, blank=False, default=None, null=True)
    stock_code = models.CharField(max_length=10, blank=False)
    stock_country = models.CharField(max_length=1, blank=False)
    vesting_type = models.CharField(max_length=1, blank=False)
    vesting_type_detail = models.CharField(max_length=1, blank=False, default=None, null=True)
    stock_name = models.CharField(max_length=15, blank=True)
    etc1_string = models.CharField(max_length=1, blank=True)
    etc2_string = models.CharField(max_length=1, blank=True)
    etc3_string = models.CharField(max_length=1, blank=True)
    etc4_string = models.CharField(max_length=1, blank=True)
    etc5_string = models.CharField(max_length=1, blank=True)
    etc1_int = models.SmallIntegerField(blank=True, null=True)
    etc2_int = models.SmallIntegerField(blank=True, null=True)
    etc3_int = models.SmallIntegerField(blank=True, null=True)
    etc4_int = models.SmallIntegerField(blank=True, null=True)
    etc5_int = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("stock_code_full","stock_code","stock_country","vesting_type","vesting_type_detail")


class StockSummaryKr(models.Model):
    bat_time = models.DateTimeField(default=datetime.now, blank = False)
    info_date = models.DateField(default=datetime.now , blank=False)
    #CharField 로 하면 varchar로 만들어짐 CharField default=5 는 varchar(5) 등
    #tinyint 는 0~ 255 까지 (1바이트) Char는 1바이트
    #smallint 는 -32,767~32,767 (2바이트)
    #int 는 -2,147,483,648 ~ 2,147,483,648 (4바이트)
    stock_code = models.CharField(max_length=10, blank=False)
    stock_country = models.CharField(max_length=1, blank=False)
    vesting_type = models.CharField(max_length=1, blank=False)
    vesting_type_detail = models.CharField(max_length=1, blank=False)
    stock_name = models.CharField(max_length=15, blank=True)
    stock_market_sum = models.IntegerField(blank=True, null=True)
    stock_share_total_num = models.IntegerField(blank=True, null=True)
    stock_first_price = models.IntegerField(blank=True, null=True)
    stock_foreign_share_max = models.IntegerField(blank=True, null=True)
    stock_foreign_share_num = models.IntegerField(blank=True, null=True)
    stock_foreign_share_percent = models.FloatField(blank=True, null=True)
    stock_maxprice_year = models.IntegerField(blank=True, null=True)
    stock_lowprice_year = models.IntegerField(blank=True, null=True)
    stock_per = models.FloatField(blank=True, null=True)
    stock_eps = models.IntegerField(blank=True, null=True)
    stock_per_guess = models.FloatField(blank=True, null=True)
    stock_eps_guess = models.IntegerField(blank=True, null=True)
    stock_pbr = models.FloatField(blank=True, null=True)
    stock_bps = models.IntegerField(blank=True, null=True)
    stock_allocation_ratio = models.FloatField(blank=True, null=True)
    stock_similar_per = models.FloatField(blank=True, null=True)
    stock_now = models.IntegerField(blank=True, null=True)
    stock_close = models.IntegerField(blank=True, null=True)
    stock_open = models.IntegerField(blank=True, null=True)
    stock_high = models.IntegerField(blank=True, null=True)
    stock_low = models.IntegerField(blank=True, null=True)
    stock_volume_share = models.IntegerField(blank=True, null=True)
    stock_volume_money = models.IntegerField(blank=True, null=True)
    stock_trading_sum_foreign = models.IntegerField(blank=True, null=True)
    stock_trading_sum_agency = models.IntegerField(blank=True, null=True)
    stock_trading_sum_ant = models.IntegerField(blank=True, null=True)
    stock_agency_buy_top1 = models.CharField(max_length=15, blank=True)
    stock_agency_buy_top1_vol = models.IntegerField(blank=True, null=True)
    stock_agency_buy_top2 = models.CharField(max_length=15, blank=True)
    stock_agency_buy_top2_vol = models.IntegerField(blank=True, null=True)
    stock_agency_buy_top3 = models.CharField(max_length=15, blank=True)
    stock_agency_buy_top3_vol = models.IntegerField(blank=True, null=True)
    stock_agency_buy_top4 = models.CharField(max_length=15, blank=True)
    stock_agency_buy_top4_vol = models.IntegerField(blank=True, null=True)
    stock_agency_buy_top5 = models.CharField(max_length=15, blank=True)
    stock_agency_buy_top5_vol = models.IntegerField(blank=True, null=True)
    stock_agency_sell_top1 = models.CharField(max_length=15, blank=True)
    stock_agency_sell_top1_vol = models.IntegerField(blank=True, null=True)
    stock_agency_sell_top2 = models.CharField(max_length=15, blank=True)
    stock_agency_sell_top2_vol = models.IntegerField(blank=True, null=True)
    stock_agency_sell_top3 = models.CharField(max_length=15, blank=True)
    stock_agency_sell_top3_vol = models.IntegerField(blank=True, null=True)
    stock_agency_sell_top4 = models.CharField(max_length=15, blank=True)
    stock_agency_sell_top4_vol = models.IntegerField(blank=True, null=True)
    stock_agency_sell_top5 = models.CharField(max_length=15, blank=True)
    stock_agency_sell_top5_vol = models.IntegerField(blank=True, null=True)
    etc1_string = models.CharField(max_length=1, blank=True)
    etc2_string = models.CharField(max_length=1, blank=True)
    etc3_string = models.CharField(max_length=1, blank=True)
    etc4_string = models.CharField(max_length=1, blank=True)
    etc5_string = models.CharField(max_length=1, blank=True)
    etc1_int = models.SmallIntegerField(blank=True, null=True)
    etc2_int = models.SmallIntegerField(blank=True, null=True)
    etc3_int = models.SmallIntegerField(blank=True, null=True)
    etc4_int = models.SmallIntegerField(blank=True, null=True)
    etc5_int = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("info_date","stock_code","stock_country","vesting_type","vesting_type_detail")


class StockCoreInfoKr(models.Model):
    bat_time = models.DateTimeField(default=datetime.now, blank = False)
    info_date = models.DateField(default=datetime.now , blank=False)
    #CharField 로 하면 varchar로 만들어짐 CharField default=5 는 varchar(5) 등
    #tinyint 는 0~ 255 까지 (1바이트) Char는 1바이트
    #smallint 는 -32,767~32,767 (2바이트)
    #int 는 -2,147,483,648 ~ 2,147,483,648 (4바이트)
    stock_code = models.CharField(max_length=10, blank=False)
    stock_country = models.CharField(max_length=1, blank=False)
    vesting_type = models.CharField(max_length=1, blank=False)
    vesting_type_detail = models.CharField(max_length=1, blank=False)
    stock_name = models.CharField(max_length=15, blank=True)
    stock_eps = models.FloatField(blank=True, null=True)
    stock_bps = models.FloatField(blank=True, null=True)
    stock_per = models.FloatField(blank=True, null=True)
    stock_similar_per = models.FloatField(blank=True, null=True)
    stock_pbr = models.FloatField(blank=True, null=True)
    stock_allocation_ratio = models.FloatField(blank=True, null=True)
    stock_first_price = models.FloatField(blank=True, null=True)
    stock_share_total_num = models.FloatField(blank=True, null=True)
    stock_current_ratio = models.FloatField(blank=True, null=True)
    stock_ratio_return_month = models.FloatField(blank=True, null=True)
    stock_ratio_return_quarter = models.FloatField(blank=True, null=True)
    stock_ratio_return_half = models.FloatField(blank=True, null=True)
    stock_ratio_return_year = models.FloatField(blank=True, null=True)
    stock_per_expectation = models.FloatField(blank=True, null=True)
    stock_per_announce = models.FloatField(blank=True, null=True)
    stock_pbr_expectation = models.FloatField(blank=True, null=True)
    stock_pbr_announce = models.FloatField(blank=True, null=True)
    stock_pcr_expectation = models.FloatField(blank=True, null=True)
    stock_pcr_announce = models.FloatField(blank=True, null=True)
    stock_ev_ebitda_expectation = models.FloatField(blank=True, null=True)
    stock_ev_ebitda_announce = models.FloatField(blank=True, null=True)
    stock_eps_expectation = models.FloatField(blank=True, null=True)
    stock_eps_announcement = models.FloatField(blank=True, null=True)
    stock_bps_expectation = models.FloatField(blank=True, null=True)
    stock_bps_announcement = models.FloatField(blank=True, null=True)
    stock_ebitda_expectation = models.FloatField(blank=True, null=True)
    stock_ebitda_announcement = models.FloatField(blank=True, null=True)
    stock_cash_dps_expectation = models.FloatField(blank=True, null=True)
    stock_cash_dps_announcement = models.FloatField(blank=True, null=True)
    stock_allocation_expectation = models.FloatField(blank=True, null=True)
    stock_allocation_announcement = models.FloatField(blank=True, null=True)
    stock_total_revenue_expq = models.FloatField(blank=True, null=True)
    stock_total_revenue_one_pastq = models.FloatField(blank=True, null=True)
    stock_total_revenue_two_pastq = models.FloatField(blank=True, null=True)
    stock_total_revenue_three_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_expq = models.FloatField(blank=True, null=True)
    stock_operating_profit_one_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_two_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_three_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_public_expq = models.FloatField(blank=True, null=True)
    stock_operating_profit_public_one_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_public_two_pastq = models.FloatField(blank=True, null=True)
    stock_operating_profit_public_three_pastq = models.FloatField(blank=True, null=True)
    stock_profit_from_continuing_expq = models.FloatField(blank=True, null=True)
    stock_profit_from_continuing_one_pastq = models.FloatField(blank=True, null=True)
    stock_profit_from_continuing_two_pastq = models.FloatField(blank=True, null=True)
    stock_profit_from_continuing_three_pastq = models.FloatField(blank=True, null=True)
    stock_netincome_expq = models.FloatField(blank=True, null=True)
    stock_netincome_one_pastq = models.FloatField(blank=True, null=True)
    stock_netincome_two_pastq = models.FloatField(blank=True, null=True)
    stock_netincome_three_pastq = models.FloatField(blank=True, null=True)
    stock_asset_expq = models.FloatField(blank=True, null=True)
    stock_asset_one_pastq = models.FloatField(blank=True, null=True)
    stock_asset_two_pastq = models.FloatField(blank=True, null=True)
    stock_asset_three_pastq = models.FloatField(blank=True, null=True)
    stock_liabilities_expq = models.FloatField(blank=True, null=True)
    stock_liabilities_one_pastq = models.FloatField(blank=True, null=True)
    stock_liabilities_two_pastq = models.FloatField(blank=True, null=True)
    stock_liabilities_three_pastq = models.FloatField(blank=True, null=True)
    stock_equity_expq = models.FloatField(blank=True, null=True)
    stock_equity_one_pastq = models.FloatField(blank=True, null=True)
    stock_equity_two_pastq = models.FloatField(blank=True, null=True)
    stock_equity_three_pastq = models.FloatField(blank=True, null=True)
    stock_capital_expq = models.FloatField(blank=True, null=True)
    stock_capital_one_pastq = models.FloatField(blank=True, null=True)
    stock_capital_two_pastq = models.FloatField(blank=True, null=True)
    stock_capital_three_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_operating_expq = models.FloatField(blank=True, null=True)
    stock_cashflow_operating_one_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_operating_two_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_operating_three_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_investing_expq = models.FloatField(blank=True, null=True)
    stock_cashflow_investing_one_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_investing_two_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_investing_three_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_financing_expq = models.FloatField(blank=True, null=True)
    stock_cashflow_financing_one_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_financing_two_pastq = models.FloatField(blank=True, null=True)
    stock_cashflow_financing_three_pastq = models.FloatField(blank=True, null=True)
    stock_capex_expq = models.FloatField(blank=True, null=True)
    stock_capex_one_pastq = models.FloatField(blank=True, null=True)
    stock_capex_two_pastq = models.FloatField(blank=True, null=True)
    stock_capex_three_pastq = models.FloatField(blank=True, null=True)
    stock_fcf_expq = models.FloatField(blank=True, null=True)
    stock_fcf_one_pastq = models.FloatField(blank=True, null=True)
    stock_fcf_two_pastq = models.FloatField(blank=True, null=True)
    stock_fcf_three_pastq = models.FloatField(blank=True, null=True)
    stock_ibl_expq = models.FloatField(blank=True, null=True)
    stock_ibl_one_pastq = models.FloatField(blank=True, null=True)
    stock_ibl_two_pastq = models.FloatField(blank=True, null=True)
    stock_ibl_three_pastq = models.FloatField(blank=True, null=True)
    stock_operating_margin_ratio_expq = models.FloatField(blank=True, null=True)
    stock_operating_margin_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_operating_margin_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_operating_margin_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_netprofit_ratio_expq = models.FloatField(blank=True, null=True)
    stock_netprofit_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_netprofit_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_netprofit_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_roe_ratio_expq = models.FloatField(blank=True, null=True)
    stock_roe_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_roe_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_roe_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_roa_ratio_expq = models.FloatField(blank=True, null=True)
    stock_roa_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_roa_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_roa_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_debt_ratio_expq = models.FloatField(blank=True, null=True)
    stock_debt_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_debt_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_debt_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_capital_retention_rate_expq = models.FloatField(blank=True, null=True)
    stock_capital_retention_rate_one_pastq = models.FloatField(blank=True, null=True)
    stock_capital_retention_rate_two_pastq = models.FloatField(blank=True, null=True)
    stock_capital_retention_rate_three_pastq = models.FloatField(blank=True, null=True)
    stock_eps_expq = models.FloatField(blank=True, null=True)
    stock_eps_one_pastq = models.FloatField(blank=True, null=True)
    stock_eps_two_pastq = models.FloatField(blank=True, null=True)
    stock_eps_three_pastq = models.FloatField(blank=True, null=True)
    stock_per_expq = models.FloatField(blank=True, null=True)
    stock_per_one_pastq = models.FloatField(blank=True, null=True)
    stock_per_two_pastq = models.FloatField(blank=True, null=True)
    stock_per_three_pastq = models.FloatField(blank=True, null=True)
    stock_bps_expq = models.FloatField(blank=True, null=True)
    stock_bps_one_pastq = models.FloatField(blank=True, null=True)
    stock_bps_two_pastq = models.FloatField(blank=True, null=True)
    stock_bps_three_pastq = models.FloatField(blank=True, null=True)
    stock_pbr_expq = models.FloatField(blank=True, null=True)
    stock_pbr_one_pastq = models.FloatField(blank=True, null=True)
    stock_pbr_two_pastq = models.FloatField(blank=True, null=True)
    stock_pbr_three_pastq = models.FloatField(blank=True, null=True)
    stock_cash_dps_expq = models.FloatField(blank=True, null=True)
    stock_cash_dps_one_pastq = models.FloatField(blank=True, null=True)
    stock_cash_dps_two_pastq = models.FloatField(blank=True, null=True)
    stock_cash_dps_three_pastq = models.FloatField(blank=True, null=True)
    stock_allocation_ratio_expq = models.FloatField(blank=True, null=True)
    stock_allocation_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_allocation_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_allocation_ratio_three_pastq = models.FloatField(blank=True, null=True)
    stock_payout_ratio_expq = models.FloatField(blank=True, null=True)
    stock_payout_ratio_one_pastq = models.FloatField(blank=True, null=True)
    stock_payout_ratio_two_pastq = models.FloatField(blank=True, null=True)
    stock_payout_ratio_three_pastq = models.FloatField(blank=True, null=True)
    etc1_string = models.CharField(max_length=1, blank=True)
    etc2_string = models.CharField(max_length=1, blank=True)
    etc3_string = models.CharField(max_length=1, blank=True)
    etc4_string = models.CharField(max_length=1, blank=True)
    etc5_string = models.CharField(max_length=1, blank=True)
    etc1_int = models.SmallIntegerField(blank=True, null=True)
    etc2_int = models.SmallIntegerField(blank=True, null=True)
    etc3_int = models.SmallIntegerField(blank=True, null=True)
    etc4_int = models.SmallIntegerField(blank=True, null=True)
    etc5_int = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("info_date","stock_code","stock_country","vesting_type","vesting_type_detail")



class StockIfrsKr(models.Model):
    bat_time = models.DateTimeField(default=datetime.now, blank = False)
    info_date = models.DateField(default=datetime.now, blank=False)
    ifrs_date = models.DateField(default=datetime.now, blank=False)
    #CharField 로 하면 varchar로 만들어짐 CharField default=5 는 varchar(5) 등
    #tinyint 는 0~ 255 까지 (1바이트) Char는 1바이트
    #smallint 는 -32,767~32,767 (2바이트)
    #int 는 -2,147,483,648 ~ 2,147,483,648 (4바이트)
    stock_code = models.CharField(max_length=5, blank=False)
    stock_country = models.CharField(max_length=1, blank=False)
    ifrs_type = models.CharField(max_length=1, blank=False)
    vesting_type = models.CharField(max_length=1, blank=False)
    vesting_type_detail = models.CharField(max_length=1, blank=False)
    stock_name = models.CharField(max_length=15, blank=True)
    stock_revenue = models.IntegerField(blank=True, null=True)
    operating_income = models.IntegerField(blank=True, null=True)
    net_income = models.IntegerField(blank=True, null=True)
    operating_income_ratio = models.FloatField(blank=True, null=True)
    income_ratio = models.FloatField(blank=True, null=True)
    roe = models.FloatField(blank=True, null=True)
    debt_ratio = models.FloatField(blank=True, null=True)
    quick_ratio = models.FloatField(blank=True, null=True)
    reserve_ratio = models.FloatField(blank=True, null=True)
    stock_eps = models.IntegerField(blank=True, null=True)
    stock_per = models.FloatField(blank=True, null=True)
    stock_bps = models.IntegerField(blank=True, null=True)
    stock_pbr = models.FloatField(blank=True, null=True)
    dividend_per_share = models.IntegerField(blank=True, null=True)
    dividend_yield_ratio = models.FloatField(blank=True, null=True)
    dividend_payout_ratio = models.FloatField(blank=True, null=True)
    etc1_string = models.CharField(max_length=1, blank=True)
    etc2_string = models.CharField(max_length=1, blank=True)
    etc3_string = models.CharField(max_length=1, blank=True)
    etc1_int = models.SmallIntegerField(blank=True, null=True)
    etc2_int = models.SmallIntegerField(blank=True, null=True)
    etc3_int = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("info_date","ifrs_date","stock_code","stock_country","ifrs_type","vesting_type","vesting_type_detail")






class TheaterWinQuestion(models.Model):
    # 토계부 질문게시판용 필드 모델
    writing_date = models.DateField(default=datetime.now, blank=False)
    question_title = models.CharField(max_length=200, blank=False)
    question_content = tinymce_models.HTMLField(blank=True)
    # isanswer 은 답변이 달렸는지에 대한 필드, 0이면 안 달리고 1이면 달린것이다.
    question_isanswer = models.IntegerField(default=0, blank=False)
    question_hit = models.IntegerField(default=0, blank=False)
    # 계층형 답변 게시물을 위한 필드
    question_groupnum = models.IntegerField(default=0, blank=False)
    question_sequencenum_ingroup = models.IntegerField(default=0, blank=False)
    question_level_ingorup = models.IntegerField(default=0, blank=False)
    # 기타 메모 및 유저 네임 필드
    etc_memo = models.CharField(blank=True, max_length=200)
    user_name = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def publish(self):
        self.writing_date = timezone.now()
        self.save()

    def __str__(self):
        return self.question_title



class TheaterWinQuestionInfo(models.Model):
    # 토계부 질문게시판용 필드 모델
    question_fk = models.ForeignKey(TheaterWinQuestion, on_delete=models.CASCADE, default=1, blank=False)
    question_thumbup = models.IntegerField(default=0, blank=False)
    question_thumbdown = models.IntegerField(default=0, blank=False)
    question_warning = models.IntegerField(default=0, blank=False)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)


class TheaterWinQuestionReply(models.Model):
    # 토계부 리플용 DB
    writing_date = models.DateField(default=datetime.now, blank=False)
    question_fk = models.ForeignKey(TheaterWinQuestion, on_delete=models.CASCADE, default=1, blank=False)
    question_reply_content = models.CharField(max_length=200)
    question_reply_thumbup = models.IntegerField(default=0, blank=False)
    question_reply_thumbdown = models.IntegerField(default=0, blank=False)
    question_reply_warning = models.IntegerField(default=0, blank=False)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    # 계층형 답변 게시물을 위한 필드
    reply_groupnum = models.IntegerField(default=0, blank=False)
    reply_sequencenum_ingroup = models.IntegerField(default=0, blank=False)
    reply_level_ingorup = models.IntegerField(default=0, blank=False)

    def publish(self):
        self.writing_date = timezone.now()
        self.save()



class Post(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    created_date2 = models.DateTimeField(default=timezone.now)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class TheaterWinBookRecord(models.Model):
    # 토계부 입력에 필요한 데이터들
    buy_date = models.DateField(default=datetime.now, blank=True)
    writing_date = models.DateField(default=datetime.now, blank=False)
    buy_game_title = models.CharField(max_length=200, blank=True)
    batting_ratio = models.FloatField(default=0, blank=True)
    batting_money = models.IntegerField(default=0, blank=True)
    folder_num = models.IntegerField(default=1, blank=True)
    win_check = models.IntegerField(default=1)
    # 장고 모델에서는 null을 허용하지 않고 blank = true로 표시한다.
    etc_memo = models.CharField(blank=True, max_length=200)
    # batting_analysis = HTMLField()
    # batting_analysis = HTMLField('Content', default='내용없음')
    # 1이 공유, 0이 비공유
    share_check = models.IntegerField(default=0)
    user_name = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    # 조회수
    hit_count = models.IntegerField(default=0, blank=True)

    def __str__(self):
        return self.buy_game_title

class TheaterWinBookRecordInfo(models.Model):
    # 토계부 질문게시판용 필드 모델
    record_fk = models.ForeignKey(TheaterWinBookRecord, on_delete=models.CASCADE, default=1, blank=False)
    record_thumbup = models.IntegerField(default=0, blank=False)
    record_thumbdown = models.IntegerField(default=0, blank=False)
    record_warning = models.IntegerField(default=0, blank=False)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)


class TheaterWinBookRecordReply(models.Model):
    # 토계부 리플용 DB
    writing_date = models.DateField(default=datetime.now, blank=False)
    record_fk = models.ForeignKey(TheaterWinBookRecord, on_delete=models.CASCADE, default=1, blank=False)
    record_reply_content = models.CharField(max_length=200)
    # CharField 는 무조건 max_length 라는 속성이 추가 되어야 함.
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    # 계층형 답변 게시물을 위한 필드
    record_groupnum = models.IntegerField(default=0, blank=False)
    record_sequencenum_ingroup = models.IntegerField(default=0, blank=False)
    record_level_ingorup = models.IntegerField(default=0, blank=False)

    def publish(self):
        self.writing_date = timezone.now()
        self.save()


class Full_Chatting_Message(models.Model):
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField()
    def __str__(self):
        return self.content


class FullvestingApi(models.Model):
    fullvesting_text = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return self.fullvesting_text




