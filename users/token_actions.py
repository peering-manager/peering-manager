from devices.models import Router

"""
Registry for token object permission custom actions.

Each model can define its available custom actions that should be controlled
by token permissions.
"""

# Registry mapping model names to their available custom actions
TOKEN_PERMISSION_ACTIONS = {}


def register_token_actions(model, actions):
    """
    Register custom actions for a model.

    Args:
        model: The model class or "app_label.model_name" string
        actions: Dict of {action_name: {label, help_text}}

    Example:
        register_token_actions(Router, {
            "configure": {
                "label": "Allow: Deploy Configuration",
                "help_text": "Allow deploying configuration to this router"
            }
        })
    """
    if isinstance(model, str):
        key = model
    else:
        key = f"{model._meta.app_label}.{model._meta.model_name}"

    TOKEN_PERMISSION_ACTIONS[key] = actions


def get_available_actions(model):
    """
    Get available custom actions for a model.

    Args:
        model: The model class or instance

    Returns:
        Dict of available actions or empty dict
    """
    # Handle both model class and instance
    if hasattr(model, "_meta"):
        key = f"{model._meta.app_label}.{model._meta.model_name}"
    else:
        key = str(model)

    return TOKEN_PERMISSION_ACTIONS.get(key, {})


register_token_actions(
    Router,
    {
        "configure": {
            "label": "Allow: Deploy Configuration",
            "help_text": "Allow deploying configuration to this router",
        },
        "configuration": {
            "label": "Allow: View Configuration",
            "help_text": "Allow viewing router configuration",
        },
        "poll_bgp_sessions": {
            "label": "Allow: Poll BGP Sessions",
            "help_text": "Allow polling BGP session states",
        },
        "test_napalm_connection": {
            "label": "Allow: Test NAPALM Connection",
            "help_text": "Allow testing NAPALM connection to router",
        },
        "push_datasource": {
            "label": "Allow: Push to Data Source",
            "help_text": "Allow pushing configuration to data sources",
        },
    },
)
