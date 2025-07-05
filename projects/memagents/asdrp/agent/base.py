#############################################################################
# base.py
#
# base class for agent replies
#
# @author Theodore Mui
# @email  theodoremui@gmail.com
# Fri Jul 04 11:30:53 PDT 2025
#############################################################################

from dataclasses import dataclass

@dataclass
class AgentReply:
    response_str: str
