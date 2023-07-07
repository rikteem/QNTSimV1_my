### Stage 1: build ###

FROM node:16.13-alpine as builder

# Set working directory.
RUN mkdir /app
WORKDIR /app

# Copy app dependencies.
COPY angular-app/package.json angular-app/package-lock.json /app/angular-app/

# Install app dependencies.
RUN npm install --prefix angular-app --force

# Copy app files.
COPY . /app

RUN chmod 775 angular-app/node_modules/.bin/ng

RUN chmod 775 angular-app/node_modules/.bin/ng.cmd
# Default build configuration.
ARG configuration=production

# Build app
RUN npm run build --prefix angular-app -- --output-path=./dist/out --configuration $configuration


## Stage 2: delivery ###

FROM nginx:1.15.7-alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy output directory from builder to nginx image.
COPY --from=builder /app/angular-app/dist/out /usr/share/nginx/html

# Copy nginx configuration file.
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf



