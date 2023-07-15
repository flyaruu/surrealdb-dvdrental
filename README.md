## Test data set for SurrealDB
This repo migrates the classic 'dvd rental' database. It's an old data set, it has been around for many years, first for MySQL and later for Postgres.

This migration script converts the SQL data model to a SurrealDB data model, hopefully in a sensible way.

CI:
[![CircleCI](https://circleci.com/gh/flyaruu/surrealdb-dvdrental.svg?style=svg)](https://circleci.com/gh/flyaruu/surrealdb-dvdrental)

I did this to get familiar with SurrealDB databases (there are no 'official' test data sets), and to develop my Rust / embedded driver for SurrealDB.

You can run it locally using the docker-compose, or use the CI-built images here:

https://hub.docker.com/repository/docker/flyaruu/surrealdb-dvdrental/general
