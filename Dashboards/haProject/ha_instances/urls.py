from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.haProject.ha_instances.views \
    import IndexView
from openstack_dashboard.dashboards.haProject.ha_instances.views \
    import AddView
from openstack_dashboard.dashboards.haProject.ha_instances.views \
    import UpdateView

INSTANCES = r'^(?P<instance_id>[^/]+)/%s$'

urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^add_to_protection/$', AddView.as_view(), name='add_to_protection'),
    url(INSTANCES % 'update',
        UpdateView.as_view(),
        name='update'),

)
