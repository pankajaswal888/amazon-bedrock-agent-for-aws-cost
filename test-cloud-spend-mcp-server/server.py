"""
AWS Cost Explorer MCP Server
Optimized version for AI agents.

Returns compact JSON instead of huge tables so the LLM
uses fewer tokens and responds faster.
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any

import boto3
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


# -----------------------------
# MCP Server
# -----------------------------

mcp = FastMCP("aws_cost_explorer")


# -----------------------------
# Models
# -----------------------------

class DaysParam(BaseModel):
    """Number of days to analyze AWS cost data"""
    days: int = Field(default=7)


# -----------------------------
# Tool 1: EC2 Spend (Last Day)
# -----------------------------

@mcp.tool(description="Returns EC2 compute spend for the last 24 hours.")
async def get_ec2_spend_last_day() -> Dict[str, Any]:

    ce_client = boto3.client("ce")

    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    response = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": ["Amazon Elastic Compute Cloud - Compute"]
            }
        }
    )

    cost = float(
        response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
    )

    return {
        "service": "EC2",
        "cost_last_day_usd": round(cost, 2)
    }


# -----------------------------
# Tool 2: Top AWS Services by Cost
# -----------------------------

@mcp.tool(description="Returns the top AWS services by cost over the specified number of days.")
async def get_detailed_breakdown_by_day(params: DaysParam) -> Dict[str, Any]:

    ce_client = boto3.client("ce")

    days = params.days

    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    try:

        response = ce_client.get_cost_and_usage(
            TimePeriod={
                "Start": start_date,
                "End": end_date
            },
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[
                {"Type": "DIMENSION", "Key": "SERVICE"}
            ]
        )

        service_totals = defaultdict(float)

        for day in response["ResultsByTime"]:
            for group in day["Groups"]:
                service = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                service_totals[service] += cost

        # Remove credits / negative values
        service_totals = {
            k: v for k, v in service_totals.items() if v > 0
        }

        top_services = sorted(
            service_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "analysis_period_days": days,
            "top_services": [
                {
                    "service": svc,
                    "cost_usd": round(cost, 2)
                }
                for svc, cost in top_services
            ]
        }

    except Exception as e:

        return {
            "error": str(e)
        }


# -----------------------------
# Tool 3: Cost Spike Detector
# -----------------------------

@mcp.tool(description="Detects abnormal AWS cost spikes compared to previous daily average.")
async def detect_cost_spike(params: DaysParam) -> Dict[str, Any]:

    ce_client = boto3.client("ce")

    days = params.days

    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"]
    )

    daily_costs = []

    for day in response["ResultsByTime"]:
        cost = float(day["Total"]["UnblendedCost"]["Amount"])
        daily_costs.append(cost)

    if len(daily_costs) < 2:
        return {"message": "Not enough data"}

    latest = daily_costs[-1]
    previous_avg = sum(daily_costs[:-1]) / (len(daily_costs) - 1)

    spike_ratio = latest / previous_avg if previous_avg > 0 else 0

    return {
        "latest_cost": round(latest, 2),
        "average_previous_cost": round(previous_avg, 2),
        "spike_ratio": round(spike_ratio, 2),
        "cost_spike_detected": spike_ratio > 1.5
    }


# -----------------------------
# Static Resource
# -----------------------------

@mcp.resource("config://app")
def get_config() -> str:
    return "AWS Cost Explorer MCP Server"


# -----------------------------
# Start MCP server
# -----------------------------

def main():

    mcp.run(
        transport=os.environ.get("MCP_TRANSPORT", "stdio")
    )


if __name__ == "__main__":
    main()
