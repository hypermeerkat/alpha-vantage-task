# Define the required provider for Azure
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Configure the Azure provider
provider "azurerm" {
  features {}
}

# Create an Azure Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "alpha-vantage-task-rg"
  location = "westeurope"
}

# Create an Azure App Service Plan
resource "azurerm_service_plan" "asp" {
  name                = "alpha-vantage-task-asp"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "F1"  # Free tier
}

# Create an Azure Web App for the backend
resource "azurerm_linux_web_app" "backend" {
  name                = "alpha-vantage-task-backend"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id

  # Configure the Docker container for the backend
  site_config {
    always_on        = false
    application_stack {
      docker_image     = "${azurerm_container_registry.acr.login_server}/backend"
      docker_image_tag = "latest"
    }
  }

  # Set environment variables and configuration for the backend
  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_REGISTRY_SERVER_URL"        = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"   = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"   = azurerm_container_registry.acr.admin_password
    "ALPHA_VANTAGE_API_KEY"             = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.alpha_vantage_api_key.id})"
    "WEBSITES_PORT"                       = "80"
    "DOCKER_ENABLE_CI"                    = "true"
    "PORT"                                = "80"
  }
}

# Create an Azure Web App for the frontend
resource "azurerm_linux_web_app" "frontend" {
  name                = "alpha-vantage-task-frontend"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id

  # Configure the Docker container for the frontend
  site_config {
    always_on        = false
    application_stack {
      docker_image     = "${azurerm_container_registry.acr.login_server}/frontend"
      docker_image_tag = "latest"
    }
  }

  # Set environment variables and configuration for the frontend
  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_REGISTRY_SERVER_URL"          = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"     = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"     = azurerm_container_registry.acr.admin_password
    "REACT_APP_BACKEND_URL"               = "https://${azurerm_linux_web_app.backend.default_hostname}"
    "WEBSITES_PORT"                       = "80"
    "DOCKER_ENABLE_CI"                    = "true"
  }
}

# Create an Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = "alphavantageacr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
}

# Create an Azure Key Vault
resource "azurerm_key_vault" "kv" {
  name                       = "daily-average-kv"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # Set access policies for the Key Vault
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge", "Recover"
    ]

    key_permissions = [
      "Get", "List", "Create", "Delete"
    ]

    certificate_permissions = [
      "Get", "List", "Create", "Delete"
    ]
  }
}

# Create a secret in the Key Vault for the Alpha Vantage API key
resource "azurerm_key_vault_secret" "alpha_vantage_api_key" {
  name         = "alpha-vantage-api-key"
  value        = var.alpha_vantage_api_key
  key_vault_id = azurerm_key_vault.kv.id
}

# Get the current Azure client configuration
data "azurerm_client_config" "current" {}

# Output the backend URL
output "backend_url" {
  value = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

# Output the frontend URL
output "frontend_url" {
  value = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}