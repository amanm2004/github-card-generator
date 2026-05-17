FROM nginx:alpine

# Copy the HTML file as a template
COPY index.html /usr/share/nginx/html/index.html.template

# Default backend URL for local testing
ENV BACKEND_URL=http://localhost:8080

# Use envsubst to replace the backend URL in the HTML template at runtime
# We specify only ${BACKEND_URL} to avoid messing with JS template literals
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'"]

EXPOSE 80
