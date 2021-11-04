import re

from drf_spectacular.openapi import AutoSchema


class PeeringManagerAutoSchema(AutoSchema):
    """
    Subclass of Spectaclar's `AutoSchema` to support bulk operations.
    """

    def get_operation_id(self):
        tokenized_path = self._tokenize_path()
        # replace dashes as they can be problematic later in code generation
        tokenized_path = [t.replace("-", "_") for t in tokenized_path]

        if self.method.lower() == "get" and self._is_list_view():
            action = "list"
        else:
            if hasattr(self.view, "action_map") and self.view.action_map:
                action = self.view.action_map[self.method.lower()]
            else:
                action = self.method_mapping[self.method.lower()]

        if not tokenized_path:
            tokenized_path.append("root")

        if re.search(r"<drf_format_suffix\w*:\w+>", self.path_regex):
            tokenized_path.append("formatted")

        return "_".join(tokenized_path + [action])
