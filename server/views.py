from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from .models import Server
from .schema import server_list_docs
from .serializer import ServerSerializer


class ServerListViewSet(viewsets.ViewSet):
    queryset = Server.objects.all()

    @server_list_docs
    def list(self, request):
        """
        Retrieve a filtered and optionally limited list of servers.

        This method processes several optional query parameters to filter, limit,
        and annotate a queryset of server objects. Depending on the provided filters,
        it can return servers by category, by the current authenticated user, or
        by a specific server ID. Optionally, it can include the number of members
        per server and limit the number of returned results.

        Authentication is required when using the `by_user` or `by_serverid` filters.

        Args:
            request (Request): The HTTP request object, expected to contain query
                parameters used for filtering the servers.

        Query Parameters:
            category (str, optional):
                The name of the category to filter servers by.
                Example: `/api/servers?category=Gaming`

            qty (int, optional):
                The maximum number of servers to return.
                Example: `/api/servers?qty=5`

            by_user (str, optional):
                If set to "true", filters servers that the authenticated user is a member of.
                Requires the user to be authenticated.
                Example: `/api/servers?by_user=true`

            by_serverid (str, optional):
                Filters the queryset to a specific server by its ID.
                Requires authentication. Raises a validation error if not found.
                Example: `/api/servers?by_serverid=42`

            with_num_members (str, optional):
                If set to "true", includes an additional `num_members` field
                in each server, representing the number of associated members.
                Example: `/api/servers?with_num_members=true`

        Raises:
            AuthenticationFailed:
                Raised if `by_user` or `by_serverid` is requested but the user is not authenticated.

            ValidationError:
                Raised if `by_serverid` is not a valid integer, or if no server
                with the given ID exists.

        Returns:
            Response: A DRF Response object containing a list of serialized server data.
                If `with_num_members=true` is provided, each serialized object will
                include a `num_members` field.

        Example:
            Request:
                GET /api/servers?category=Education&qty=10&with_num_members=true

            Response:
                [
                    {
                        "id": 1,
                        "name": "Study Group A",
                        "category": "Education",
                        "num_members": 45
                    },
                    ...
                ]
        """

        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        if category:
            self.queryset = self.queryset.filter(category__name=category)

        if by_user:
            if by_user and request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            else:
                raise AuthenticationFailed()

        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(
                        detail=f"Server with id {by_serverid} not found.",
                    )
            except ValueError:
                raise ValidationError(
                    detail="Server value error",
                )

        if qty:
            self.queryset = self.queryset[: int(qty)]

        serializer = ServerSerializer(
            self.queryset, many=True, context={"num_members": with_num_members}
        )

        return Response(serializer.data)
