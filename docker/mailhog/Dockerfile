# build stage
FROM golang:1.24-alpine AS builder
RUN apk add --no-cache git && go install github.com/mailhog/MailHog@latest

# final image
FROM debian:bookworm-slim

RUN apt update && apt install -y dos2unix && apt clean

COPY --from=builder /go/bin/MailHog /usr/local/bin/MailHog
COPY commands/setup_mailhog_auth.sh /commands/setup_mailhog_auth.sh

RUN dos2unix /commands/setup_mailhog_auth.sh && chmod +x /commands/setup_mailhog_auth.sh

ENTRYPOINT ["/commands/setup_mailhog_auth.sh"]