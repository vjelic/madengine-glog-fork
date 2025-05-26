"""
Copyright (c) Advanced Micro Devices, Inc. All rights reserved.
"""
r'''
# What is MADEngine?

An AI Models automation and dashboarding command-line tool to run LLMs and Deep Learning models locally or remotelly with CI. 
The MADEngine library is to support AI automation having following features:
- AI Models run reliably on supported platforms and drive software quality
- Simple, minimalistic, out-of-the-box solution that enable confidence on hardware and software stack
- Real-time, audience-relevant AI Models performance metrics tracking, presented in clear, intuitive manner
- Best-practices for handling internal projects and external open-source projects



.. include:: ../../docs/how-to-build.md
.. include:: ../../docs/how-to-quick-start.md
.. include:: ../../docs/how-to-provide-contexts.md
.. include:: ../../docs/how-to-profile-a-model.md
.. include:: ../../docs/how-to-collect-competitive-library-perf.md
.. include:: ../../docs/how-to-contribute.md

'''
from importlib.metadata import version

__version__ = version("madengine")