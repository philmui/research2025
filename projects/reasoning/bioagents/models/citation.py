#------------------------------------------------------------------------------
# citation.py
# 
# This is a data class for citations. It provides a common interface for all citations.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------


from dataclasses import dataclass

@dataclass
class Citation:
    url: str
    title: str
    snippet: str
    source: str
    