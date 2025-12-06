#############################################################################
# dict_utils.py
#
# Dictionary utility functions for building parameter dictionaries.
#
# This module provides utility functions for working with dictionaries,
# particularly for building parameter dictionaries that filter out None and
# empty values. This is commonly needed when constructing API request
# parameters where optional parameters should only be included if they have
# meaningful values.
#
# Design Principles:
# - Single Responsibility: Each function has one clear purpose
# - Immutability: Functions return new dictionaries rather than modifying inputs
# - Type Safety: Full type hints for better IDE support and error detection
# - Documentation: Comprehensive docstrings with examples
#
#############################################################################

from typing import Any, Dict, Optional, Callable


class DictUtils:
    """
    Utility class for dictionary operations.
    
    This class provides static methods for common dictionary operations,
    particularly useful for building parameter dictionaries for API calls
    where optional parameters should be conditionally included.
    
    All methods are static, so the class never needs to be instantiated.
    This follows the utility class pattern where the class serves as a
    namespace for related functions.
    
    Examples:
    --------
    >>> # Basic usage - filter out None and empty values
    >>> params = DictUtils.build_params(
    ...     required='value',
    ...     optional=None,
    ...     empty='',
    ...     zero=0,
    ...     false=False
    ... )
    >>> params
    {'required': 'value'}
    
    >>> # Include zero values
    >>> params = DictUtils.build_params(
    ...     count=0,
    ...     name='test',
    ...     include_zero=True
    ... )
    >>> params
    {'count': 0, 'name': 'test'}
    
    >>> # Custom filter function
    >>> def not_none(value):
    ...     return value is not None
    >>> params = DictUtils.build_params(
    ...     a=1,
    ...     b=None,
    ...     c='',
    ...     filter_func=not_none
    ... )
    >>> params
    {'a': 1, 'c': ''}
    """
    
    @staticmethod
    def build_params(
        *,
        include_zero: bool = False,
        include_false: bool = False,
        include_empty_string: bool = False,
        filter_func: Optional[Callable[[Any], bool]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Build a parameter dictionary, filtering out None and optionally other falsy values.
        
        This method creates a clean parameter dictionary by filtering out unwanted
        values. By default, it filters out None, empty strings, 0, and False.
        This is useful when building API request parameters where optional parameters
        should only be included if they have meaningful values.
        
        Args:
            include_zero: If True, include zero (0) values in the result.
                Default: False
            include_false: If True, include False boolean values in the result.
                Default: False
            include_empty_string: If True, include empty strings ('') in the result.
                Default: False
            filter_func: Optional custom filter function that takes a value and
                returns True if the value should be included. If provided, this
                overrides the default filtering logic. The function signature
                should be: `(value: Any) -> bool`
            **kwargs: Key-value pairs where values are conditionally included
                based on the filtering rules.
        
        Returns:
            Dict[str, Any]: Dictionary containing only values that pass the
                filtering criteria. Keys are preserved as provided.
        
        Raises:
            TypeError: If filter_func is provided but not callable.
        
        Examples:
        --------
        Basic usage - filter out None and empty values:
        >>> DictUtils.build_params(required='value', optional=None, empty='')
        {'required': 'value'}
        
        Include zero values:
        >>> DictUtils.build_params(count=0, name='test', include_zero=True)
        {'count': 0, 'name': 'test'}
        
        Include False boolean values:
        >>> DictUtils.build_params(enabled=False, name='test', include_false=True)
        {'enabled': False, 'name': 'test'}
        
        Include empty strings:
        >>> DictUtils.build_params(description='', name='test', include_empty_string=True)
        {'description': '', 'name': 'test'}
        
        Custom filter function (only exclude None):
        >>> def not_none(value):
        ...     return value is not None
        >>> DictUtils.build_params(a=1, b=None, c='', filter_func=not_none)
        {'a': 1, 'c': ''}
        
        Real-world API parameter building:
        >>> params = DictUtils.build_params(
        ...     location=(37.7749, -122.4194),
        ...     radius=1000,
        ...     keyword='restaurant',
        ...     type=None,  # Will be filtered out
        ...     language='en'
        ... )
        >>> params
        {'location': (37.7749, -122.4194), 'radius': 1000, 'keyword': 'restaurant', 'language': 'en'}
        """
        if filter_func is not None:
            if not callable(filter_func):
                raise TypeError(
                    f"filter_func must be callable, got {type(filter_func).__name__}"
                )
            return {k: v for k, v in kwargs.items() if filter_func(v)}
        
        # Default filtering logic
        result = {}
        for key, value in kwargs.items():
            # Always exclude None
            if value is None:
                continue
            
            # Check if value is falsy (but not None, which we already checked)
            if not value:
                # Include based on flags
                if isinstance(value, bool) and value is False:
                    if include_false:
                        result[key] = value
                elif isinstance(value, (int, float)) and value == 0:
                    if include_zero:
                        result[key] = value
                elif isinstance(value, str) and value == '':
                    if include_empty_string:
                        result[key] = value
                # Other falsy values (empty list, empty dict, etc.) are excluded
            else:
                # Truthy values are always included
                result[key] = value
        
        return result
    
    @staticmethod
    def filter_none(**kwargs: Any) -> Dict[str, Any]:
        """
        Build a parameter dictionary, filtering out only None values.
        
        This is a convenience method that calls build_params with filter_func
        set to only exclude None values. All other values (including 0, False,
        empty strings) are included.
        
        Args:
            **kwargs: Key-value pairs where None values are filtered out.
        
        Returns:
            Dict[str, Any]: Dictionary containing all non-None values.
        
        Examples:
        --------
        >>> DictUtils.filter_none(a=1, b=None, c=0, d=False, e='')
        {'a': 1, 'c': 0, 'd': False, 'e': ''}
        """
        return DictUtils.build_params(
            filter_func=lambda v: v is not None,
            **kwargs
        )
    
    @staticmethod
    def filter_falsy(**kwargs: Any) -> Dict[str, Any]:
        """
        Build a parameter dictionary, filtering out all falsy values.
        
        This is a convenience method that filters out None, 0, False, empty
        strings, empty lists, empty dicts, etc. Only truthy values are included.
        
        Args:
            **kwargs: Key-value pairs where falsy values are filtered out.
        
        Returns:
            Dict[str, Any]: Dictionary containing only truthy values.
        
        Examples:
        --------
        >>> DictUtils.filter_falsy(a=1, b=None, c=0, d=False, e='', f=[], g={})
        {'a': 1}
        
        >>> DictUtils.filter_falsy(name='test', count=5, enabled=True)
        {'name': 'test', 'count': 5, 'enabled': True}
        """
        return DictUtils.build_params(**kwargs)

