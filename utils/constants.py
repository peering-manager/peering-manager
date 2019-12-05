COLOR_CHOICES = (
    ("aa1409", "Dark red"),
    ("f44336", "Red"),
    ("e91e63", "Pink"),
    ("ffe4e1", "Rose"),
    ("ff66ff", "Fuschia"),
    ("9c27b0", "Purple"),
    ("673ab7", "Dark purple"),
    ("3f51b5", "Indigo"),
    ("2196f3", "Blue"),
    ("03a9f4", "Light blue"),
    ("00bcd4", "Cyan"),
    ("009688", "Teal"),
    ("00ffff", "Aqua"),
    ("2f6a31", "Dark green"),
    ("4caf50", "Green"),
    ("8bc34a", "Light green"),
    ("cddc39", "Lime"),
    ("ffeb3b", "Yellow"),
    ("ffc107", "Amber"),
    ("ff9800", "Orange"),
    ("ff5722", "Dark orange"),
    ("795548", "Brown"),
    ("c0c0c0", "Light grey"),
    ("9e9e9e", "Grey"),
    ("607d8b", "Dark grey"),
    ("111111", "Black"),
    ("ffffff", "White"),
)

# Object change log actions
OBJECT_CHANGE_ACTION_CREATE = 1
OBJECT_CHANGE_ACTION_UPDATE = 2
OBJECT_CHANGE_ACTION_DELETE = 3
OBJECT_CHANGE_ACTION_CHOICES = (
    (OBJECT_CHANGE_ACTION_CREATE, "Created"),
    (OBJECT_CHANGE_ACTION_UPDATE, "Updated"),
    (OBJECT_CHANGE_ACTION_DELETE, "Deleted"),
)

# User Actions Constants
USER_ACTION_CREATE = 1
USER_ACTION_EDIT = 2
USER_ACTION_DELETE = 3
USER_ACTION_IMPORT = 4
USER_ACTION_BULK_DELETE = 5
USER_ACTION_BULK_EDIT = 6
USER_ACTION_CHOICES = (
    (USER_ACTION_CREATE, "created"),
    (USER_ACTION_EDIT, "modified"),
    (USER_ACTION_DELETE, "deleted"),
    (USER_ACTION_IMPORT, "imported"),
    (USER_ACTION_BULK_DELETE, "bulk deleted"),
    (USER_ACTION_BULK_EDIT, "bulk modified"),
)
