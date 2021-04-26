class PolicyMixin(object):
    """
    This mixin defines functions that needs to be implemented by classes having
    routing policies fields.

    If the concrete model is not to be used in templates (email and config), this
    mixin does not need to be implemented.
    """

    def export_policies(self):
        """
        Returns a QuerySet of all routing policies to evaluate on export.
        """
        raise NotImplementedError()

    def import_policies(self):
        """
        Returns a QuerySet of all routing policies to evaluate on import.
        """
        raise NotImplementedError()

    def policies(self):
        """
        Returns a QuerySet of all routing policies.
        """
        return self.export_policies() & self.import_policies()
