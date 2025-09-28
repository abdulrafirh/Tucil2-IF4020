from app import create_app

# Create an app instance from the app factory
app = create_app()

if __name__ == '__main__':
    # The host must be '0.0.0.0' to be accessible from the Docker container
    app.run(host='0.0.0.0', port=8080, debug=True)
