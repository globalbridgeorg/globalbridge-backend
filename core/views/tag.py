from rest_framework.viewsets import ReadOnlyModelViewSet
from core.models import Tag
from core.serializers import TagSerializer

class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
