from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Block, Report
from accounts.models import User
from .serializers import BlockSerializer, ReportSerializer

class BlockListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blocks = Block.objects.filter(blocker=request.user)
        return Response(BlockSerializer(blocks, many=True).data)

    def post(self, request):
        blocked_user_id = request.data.get('blocked_user_id')
        if not blocked_user_id:
            return Response({'error': 'blocked_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
            block, _ = Block.objects.get_or_create(blocker=request.user, blocked=blocked_user)
            return Response(BlockSerializer(block).data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class BlockDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, user_id):
        Block.objects.filter(blocker=request.user, blocked_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ReportListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reports = Report.objects.filter(reporter=request.user)
        return Response(ReportSerializer(reports, many=True).data)

    def post(self, request):
        reported_user_id = request.data.get('reported_user_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')

        if not reported_user_id or not reason:
            return Response({'error': 'reported_user_id and reason are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            reported_user = User.objects.get(id=reported_user_id)
            report = Report.objects.create(
                reporter=request.user,
                reported_user=reported_user,
                reason=reason,
                description=description
            )
            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
