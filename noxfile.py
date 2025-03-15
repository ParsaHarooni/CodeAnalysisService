import nox


@nox.session(python=["3.11"])
def tests(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("pytest")


@nox.session(python=["3.11"])
def lint(session):
    session.install("poetry")
    session.run("poetry", "install")
    session.run("black", ".")


@nox.session(python=["3.11"])
def type_check(session):
    session.install("poetry")
    session.run("poetry", "install")
