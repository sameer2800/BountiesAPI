from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from std_bounties import views


router = DefaultRouter()

router.register(r'^bounty/draft', views.DraftBountyWriteViewSet)
router.register(r'^bounty', views.BountyViewSet)
router.register(r'^fulfillment', views.FulfillmentViewSet)
router.register(r'^category', views.CategoryViewSet)

urlpatterns = [
    url(r'^languages/$', views.Languages.as_view()),
    url(r'^leaderboard/issuer/$', views.LeaderboardIssuer.as_view()),
    url(r'^leaderboard/fulfiller/$', views.LeaderboardFulfiller.as_view()),
    url(r'^token/$', views.Tokens.as_view()),
    url(r'^bounty/(?P<bounty_id>\d+)/fulfillment/(?P<fulfillment_id>\d+)/review/$', views.SubmissionReviews.as_view()),
    url(r'^bounty/(?P<bounty_id>\d+)/comment/$', views.BountyComments.as_view()),
    url(r'^', include(router.urls)),
]
