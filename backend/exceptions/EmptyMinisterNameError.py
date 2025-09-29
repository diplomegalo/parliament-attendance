class EmptyMinisterNameError(Exception):
    """Exception raised for errors in the minister name.

    Attributes:
        name -- input name which caused the error
        message -- explanation of the error
    """

    def __init__(self, message="Minister name cannot be empty."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
