FROM node:14-alpine3.14

RUN mkdir /app
WORKDIR /app
ADD . /app

RUN yarn install

EXPOSE 8545

ENV BLOCK_NUMBER=11844372
ENV KEY=WIedVERFqJW1Rlc5Yg6hshrLSCGqzXru
ENV NETWORK=ropsten

CMD [ "yarn", "fork" ]