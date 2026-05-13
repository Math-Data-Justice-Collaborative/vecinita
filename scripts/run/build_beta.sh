#!/bin/bash
# run/build_beta.sh

echo "🐳 Building Vecinita BETA image..."

# We assume this is run from the project root
# so '.' refers to the folder containing the Dockerfile
docker build -t vecinita:beta .

echo "✅ Build complete!"
