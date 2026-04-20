# SPDX-License-Identifier: MIT
# Hello-world AlgoPy contract for end-to-end toolchain verification.

from algopy import ARC4Contract, arc4


class HelloWorld(ARC4Contract):
    @arc4.abimethod(create="require")
    def create(self) -> None:
        pass

    @arc4.abimethod
    def hello(self, name: arc4.String) -> arc4.String:
        return name
