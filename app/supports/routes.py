from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.services.dbServices import connect_to_database
from app.supports.schemas import (
    SupportTicketCreate,
    SupportTicketUpdate,
    SupportTicketResponse,
)
from app.auth.token import verify_token
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")


@router.post("/support/ticket", response_model=SupportTicketResponse)
async def create_ticket(
    ticket: SupportTicketCreate, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user_record = cursor.fetchone()

        if user_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_id = user_record[0]

        cursor.execute(
            """
            INSERT INTO SupportTickets (userId, subject, message, status, createdAt, updatedAt)
            VALUES (?, ?, ?, 'Open', GETDATE(), GETDATE())
            """,
            (user_id, ticket.subject, ticket.message),
        )

        conn.commit()

        cursor.execute(
            "SELECT * FROM SupportTickets WHERE userId=? ORDER BY createdAt DESC",
            (user_id,),
        )
        new_ticket = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_ticket:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving new ticket",
            )

        return {
            "ticket_id": new_ticket[0],
            "user_id": new_ticket[1],
            "subject": new_ticket[2],
            "message": new_ticket[3],
            "status": new_ticket[4],
            "created_at": format_datetime(new_ticket[5]),
            "updated_at": format_datetime(new_ticket[6]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating support ticket",
        )


@router.get("/support/tickets", response_model=List[SupportTicketResponse])
async def get_tickets(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user_record = cursor.fetchone()

        if user_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_id = user_record[0]

        cursor.execute("SELECT * FROM SupportTickets WHERE userId=?", (user_id,))
        tickets = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "ticket_id": item[0],
                "user_id": item[1],
                "subject": item[2],
                "message": item[3],
                "status": item[4],
                "created_at": format_datetime(item[5]),
                "updated_at": format_datetime(item[6]),
            }
            for item in tickets
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching support tickets",
        )


@router.get("/support/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(ticket_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        conn = await connect_to_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user_record = cursor.fetchone()
        
        if user_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_id = user_record[0]
        
        cursor.execute(
            "SELECT * FROM SupportTickets WHERE ticketId=? AND userId=?",
            (ticket_id, user_id),
        )
        ticket = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        
        return {
            "ticket_id": ticket[0],
            "user_id": ticket[1],
            "subject": ticket[2],
            "message": ticket[3],
            "status": ticket[4],
            "created_at": format_datetime(ticket[5]),
            "updated_at": format_datetime(ticket[6]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching ticket details",
        )


@router.put("/support/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: SupportTicketUpdate,
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        conn = await connect_to_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user_record = cursor.fetchone()
        
        if user_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_id = user_record[0]
        
        cursor.execute(
            "SELECT * FROM SupportTickets WHERE ticketId=? AND userId=?",
            (ticket_id, user_id),
        )
        existing_ticket = cursor.fetchone()
        
        if not existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
            )
        
        cursor.execute(
            """
            UPDATE SupportTickets
            SET subject=?, message=?, status=?, updatedAt=GETDATE()
            WHERE ticketId=? AND userId=?
            """,
            (
                ticket_update.subject,
                ticket_update.message,
                ticket_update.status,
                ticket_id,
                user_id,
            ),
        )
        conn.commit()
        
        cursor.execute(
            "SELECT * FROM SupportTickets WHERE ticketId=? AND userId=?",
            (ticket_id, user_id),
        )
        updated_ticket = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Failed to update ticket"
            )
        
        return {
            "ticket_id": updated_ticket[0],
            "user_id": updated_ticket[1],
            "subject": updated_ticket[2],
            "message": updated_ticket[3],
            "status": updated_ticket[4],
            "created_at": format_datetime(updated_ticket[5]),
            "updated_at": format_datetime(updated_ticket[6]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating ticket",
        )


@router.delete("/support/tickets/{ticket_id}", status_code=status.HTTP_200_OK)
async def delete_ticket(ticket_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        conn = await connect_to_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user_record = cursor.fetchone()
        
        if user_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_id = user_record[0]
        
        cursor.execute(
            "SELECT * FROM SupportTickets WHERE ticketId=? AND userId=?",
            (ticket_id, user_id),
        )
        existing_ticket = cursor.fetchone()
        
        if not existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
            )
        
        cursor.execute(
            "DELETE FROM SupportTickets WHERE ticketId=? AND userId=?",
            (ticket_id, user_id),
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "message": "Ticket successfully deleted"
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting ticket",
        )