from maya import OpenMaya as legacy

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MPyContext(object):
    """
    Context hook that alters the `MDGContext` at runtime.
    This allows `MPyAttribute` instances to evaluate the DAG at a different times.
    """

    __slots__ = ('time', 'context', 'contextGuard')

    def __init__(self, time):
        """
        Private method called after a new instance is created.

        :type time: Union[int, float, None]
        :rtype: None
        """

        # Call parent method
        #
        super(MPyContext, self).__init__()

        # Declare public variables
        #
        self.time = legacy.MTime(0, legacy.MTime.uiUnit())
        self.context = legacy.MDGContext.current()
        self.contextGuard = None

        if isinstance(time, (int, float)):

            self.time.setValue(time)
            self.context = legacy.MDGContext(self.time)

    def __enter__(self):
        """
        Private method called before a block of code is executed.

        :rtype: None
        """

        # Check if context guard is required
        #
        if not self.context.isNormal() or not self.context.isCurrent():

            log.info(f'Creating context guard @ {self.time.value()}')
            self.contextGuard = legacy.MDGContextGuard(self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method called after a block of code has been executed.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: str
        :rtype: None
        """

        # Check if context guard should be removed
        #
        if self.contextGuard is not None:

            log.debug(f'Removing context guard @ {self.time.value()}')
            self.contextGuard = None
