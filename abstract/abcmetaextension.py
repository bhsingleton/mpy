from abc import ABCMeta


class ABCMetaExtension(ABCMeta):
    """
    Extension of ABC's metaclass that implements post-initialization.
    """

    __slots__ = ()

    def __call__(cls, *args, **kwargs):
        """
        Private method that's called whenever this class is evoked.

        :rtype: QMetaclass
        """

        instance = super(ABCMetaExtension, cls).__call__(*args, **kwargs)
        instance.__post_init__(*args, **kwargs)

        return instance
