"""Regulator value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Regulator:
  code: str
  name: str
  jurisdiction: str
