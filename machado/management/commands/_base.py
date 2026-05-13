# Copyright 2026 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

from django.core.management.base import CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.utils import IntegrityError
from machado.models import History
from machado.loaders.exceptions import ImportingError


class HistoryCommandMixin:
    """
    Mixin to automatically handle History logging for management commands.
    Logs start, success, and data-related failures.
    """

    def execute(self, *args, **options):
        history_obj = History()
        # Get the command name from the module path
        command_name = self.__class__.__module__.split(".")[-1]

        # Capture parameters
        params = str(options)

        history_obj.start(command=command_name, params=params)

        try:
            output = super().execute(*args, **options)
            history_obj.success(description="Done")
            return output
        except (
            ImportingError,
            ObjectDoesNotExist,
            MultipleObjectsReturned,
            IntegrityError,
        ) as e:
            history_obj.failure(description=str(e))
            # Re-raise as CommandError if it's not already one, or just re-raise
            if not isinstance(e, CommandError):
                raise CommandError(e)
            raise e
        except Exception as e:
            # For non-data-related errors, we don't log to history as per user request
            # But we should still allow the exception to propagate
            raise e
